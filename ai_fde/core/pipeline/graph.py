"""The LangGraph StateGraph for one pipeline stage's generate/validate/repair/gate loop.

One compiled graph is built per stage per run (cheap -- these are small graphs),
closing over the concrete LLMClient, PromptRegistry, PipelineConfig, and the
run's parsed documents. Graph *state* only ever holds JSON-safe values (str,
int, bool, dict, list) -- never a pydantic model or a live client -- so it
serializes cleanly through the SQLite checkpointer.

Node topology, matching the build spec exactly:

    generate -> check_sections -> route(validate | repair | finalize)
                                                       validate -> route(pass | repair)
                                    repair -> check_sections (loop) -^
                                                       finalize -> gate

`check_sections` enforces the generator prompt's `required_sections` (front
matter, never otherwise read) deterministically -- a regex over `##` headings,
no LLM call -- before a real validator call is spent on a draft that is
structurally incomplete. A miss produces a synthetic ValidationReport-shaped
issue list (same schema `validate_node` produces) and routes straight to
`repair`, so `repair_node` and `finalize_node` need no awareness that the
failure was structural rather than a validator's judgement call.

`route_after_validate` and `route_after_check_sections` share one structural
guarantee, not a counter someone can get wrong later: attempt_number >= 2
always routes to finalize, never back to repair -- "only one repair attempt,
ever" is enforced by the graph's edges, not by a runtime check that could
regress.

`gate` calls `interrupt()` only in stepwise mode. Resuming with
`Command(resume={"action": "approve"|"edit"|"regenerate", ...})` either ends
the stage (approve/edit) or loops back to `generate` with a steering note
(regenerate) -- verified against the installed langgraph version's actual
interrupt/resume semantics before writing this (see scratchpad/lg_probe*.py).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import interrupt
from pydantic import ValidationError

from ai_fde.core.models import ParsedDocument, StageArtifact
from ai_fde.core.pipeline.config import PipelineConfig, StageConfig
from ai_fde.core.ports import LLMClient
from ai_fde.core.prompts.composer import compose_generation_prompt, compose_repair_prompt, compose_validation_prompt
from ai_fde.core.prompts.registry import PromptRegistry
from ai_fde.core.settings import Settings
from ai_fde.core.validation.models import ValidationReport


class AttemptRecord(TypedDict):
    content: str
    prompt_id: str
    generator_model: str
    validation_report: dict[str, Any] | None


class StageGraphState(TypedDict, total=False):
    mode: Literal["auto", "stepwise"]
    threshold: int
    max_repair_attempts: int
    draft: str
    attempt_number: int
    attempts_log: list[AttemptRecord]
    missing_sections: list[str]
    validation_report: dict[str, Any] | None
    validation_unavailable: bool
    needs_review: bool
    repaired: bool
    edited_by_user: bool
    regenerate_count: int
    resume_action: dict[str, Any] | None


_logger = logging.getLogger("ai_fde.pipeline")

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)

_OUTER_MARKDOWN_FENCE_RE = re.compile(r"\A\s*```[ \t]*[A-Za-z]*[ \t]*\n(?P<inner>.*)\n```\s*\Z", re.DOTALL)

_H2_HEADING_RE = re.compile(r"(?m)^##[ \t]+(.+?)[ \t]*$")


def _find_missing_sections(draft: str, required_sections: list[str]) -> list[str]:
    present = {h.strip().lower() for h in _H2_HEADING_RE.findall(draft)}
    return [s for s in required_sections if s.strip().lower() not in present]


def _missing_sections_report(missing: list[str]) -> dict[str, Any]:
    """A ValidationReport-shaped dict (same schema `validate_node` produces) built
    deterministically from a `##`-heading scan -- never from an LLM call. Keeping
    the exact shape lets this flow through `repair_node`/`finalize_node` unchanged:
    they cannot tell a structural miss from a validator's judgement call, and
    don't need to."""
    section_list = ", ".join(f"'{s}'" for s in missing)
    return {
        "overall_score": 0,
        "verdict": "fail",
        "criteria": [
            {
                "name": "structural_completeness",
                "score": 0,
                "weight": 1.0,
                "comment": f"Missing required section(s): {section_list}.",
            }
        ],
        "issues": [
            {
                "severity": "critical",
                "location": "document structure",
                "problem": f"Required section '## {s}' is missing from the artifact.",
                "fix": f"Add a '## {s}' section with real content per the stage prompt's Output/Produce list.",
            }
            for s in missing
        ],
        "repair_instructions": (
            "This draft is missing required sections and was rejected before reaching the "
            f"validator model. Add the following '##' sections, each with real content per the "
            f"stage prompt: {section_list}."
        ),
    }


def _strip_outer_markdown_fence(text: str) -> str:
    """Generator models frequently wrap an entire Markdown artifact in one
    outer ```markdown ... ``` fence despite being asked for raw Markdown --
    left in place, the whole artifact renders as one literal code block in the
    UI and the fence markers end up as text in the bundled .md file. Strip
    only a fence that wraps the *entire* response (anchored to \\A/\\Z), so
    fenced code blocks that are actually part of the content (e.g. a Mermaid
    or PlantUML diagram) are left untouched."""
    match = _OUTER_MARKDOWN_FENCE_RE.match(text.strip())
    return match.group("inner") if match else text


def _extract_json_candidate(raw: str) -> str:
    """Real validator models routinely wrap JSON in markdown fences or add a
    sentence of prose despite being told not to (reasoning-class models
    especially). Try progressively looser extraction before giving up, rather
    than failing on the first character that isn't `{`."""
    raw = raw.strip()
    fence_match = _JSON_FENCE_RE.search(raw)
    if fence_match:
        return fence_match.group(1)
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start : end + 1]
    return raw


def _try_parse_report(raw: str) -> tuple[ValidationReport | None, str | None]:
    candidate = _extract_json_candidate(raw)
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        _logger.warning("validator response was not parseable JSON: %s | raw (first 500 chars): %r", exc, raw[:500])
        return None, f"response was not valid JSON: {exc}"
    try:
        return ValidationReport.model_validate(payload), None
    except ValidationError as exc:
        _logger.warning("validator response failed schema validation: %s | raw (first 500 chars): %r", exc, raw[:500])
        return None, f"response did not match the validation schema: {exc}"


def build_stage_graph(
    *,
    llm_client: LLMClient,
    registry: PromptRegistry,
    pipeline: PipelineConfig,
    stage: StageConfig,
    generator_prompt_id: str,
    use_case: ParsedDocument,
    evidence: list[ParsedDocument],
    prior_artifacts: list[StageArtifact],
    settings: Settings,
    domain_config: dict[str, str],
    checkpointer: Any,
) -> CompiledStateGraph:
    required_sections = registry.get(generator_prompt_id).front_matter.required_sections

    async def generate_node(state: StageGraphState) -> dict[str, Any]:
        resume_action = state.get("resume_action") or {}
        note = resume_action.get("note") if resume_action.get("action") == "regenerate" else None
        regenerate_count = state.get("regenerate_count", 0)
        if resume_action.get("action") == "regenerate":
            regenerate_count += 1

        system, user = compose_generation_prompt(
            registry=registry,
            pipeline=pipeline,
            generator_prompt_id=generator_prompt_id,
            use_case=use_case,
            evidence=evidence,
            prior_artifacts=prior_artifacts,
            domain_config=domain_config,
        )
        if note:
            user = (
                f"{user}\n\n---\n\n## Steering note from the reviewer\n\n{note}\n\n"
                "Regenerate the artifact taking this note into account.\n"
            )

        response = await llm_client.complete(model=settings.generator_model, system=system, prompt=user)
        content = _strip_outer_markdown_fence(response.content)

        return {
            "draft": content,
            "attempt_number": 1,
            "attempts_log": [
                {
                    "content": content,
                    "prompt_id": generator_prompt_id,
                    "generator_model": settings.generator_model,
                    "validation_report": None,
                }
            ],
            "validation_report": None,
            "validation_unavailable": False,
            "needs_review": False,
            "repaired": False,
            "edited_by_user": False,
            "regenerate_count": regenerate_count,
            "resume_action": None,
        }

    async def validate_node(state: StageGraphState) -> dict[str, Any]:
        draft = state["draft"]
        system, user = compose_validation_prompt(
            registry=registry,
            pipeline=pipeline,
            validator_prompt_id=stage.validator,
            use_case=use_case,
            evidence=evidence,
            prior_artifacts=prior_artifacts,
            draft=draft,
            domain_config=domain_config,
        )

        validator_model = stage.validator_model or settings.validator_model
        response = await llm_client.complete(model=validator_model, system=system, prompt=user)
        report, error = _try_parse_report(response.content)

        if report is None:
            retry_prompt = (
                f"{user}\n\n---\n\nYour previous response failed schema validation: {error}\n"
                "Return ONLY the JSON object matching the schema. No prose, no code fences."
            )
            response2 = await llm_client.complete(
                model=validator_model, system=system, prompt=retry_prompt
            )
            report, error = _try_parse_report(response2.content)

        attempts_log = list(state.get("attempts_log", []))
        report_dict = report.model_dump() if report is not None else None
        if attempts_log:
            attempts_log[-1] = {**attempts_log[-1], "validation_report": report_dict}

        return {
            "validation_report": report_dict,
            "validation_unavailable": report is None,
            "attempts_log": attempts_log,
        }

    async def check_sections_node(state: StageGraphState) -> dict[str, Any]:
        if not required_sections:
            return {"missing_sections": []}

        missing = _find_missing_sections(state["draft"], required_sections)
        if not missing:
            return {"missing_sections": []}

        report_dict = _missing_sections_report(missing)
        attempts_log = list(state.get("attempts_log", []))
        if attempts_log:
            attempts_log[-1] = {**attempts_log[-1], "validation_report": report_dict}

        return {
            "missing_sections": missing,
            "validation_report": report_dict,
            "validation_unavailable": False,
            "attempts_log": attempts_log,
        }

    def route_after_check_sections(state: StageGraphState) -> str:
        if not state.get("missing_sections"):
            return "validate"
        repairs_used = state.get("attempt_number", 1) - 1
        if repairs_used >= state.get("max_repair_attempts", 1):
            return "finalize"
        return "repair"

    def route_after_validate(state: StageGraphState) -> str:
        if state.get("validation_unavailable"):
            return "finalize"
        # MAX_REPAIR_ATTEMPTS (env, default 1) caps repairs per stage; 0 disables
        # repair entirely without deleting the repair node -- attempt_number - 1
        # is "repairs already used", so this is the only place that number is
        # compared against the configured cap.
        repairs_used = state.get("attempt_number", 1) - 1
        if repairs_used >= state.get("max_repair_attempts", 1):
            return "finalize"
        report = state["validation_report"]
        assert report is not None
        if report["overall_score"] >= state["threshold"]:
            return "finalize"
        return "repair"

    async def repair_node(state: StageGraphState) -> dict[str, Any]:
        _, original_user = compose_generation_prompt(
            registry=registry,
            pipeline=pipeline,
            generator_prompt_id=generator_prompt_id,
            use_case=use_case,
            evidence=evidence,
            prior_artifacts=prior_artifacts,
            domain_config=domain_config,
        )
        system, user = compose_repair_prompt(
            registry=registry,
            pipeline=pipeline,
            original_prompt=original_user,
            failed_draft=state["draft"],
            validation_report_json=json.dumps(state["validation_report"]),
            domain_config=domain_config,
        )
        validator_model = stage.validator_model or settings.validator_model
        response = await llm_client.complete(model=validator_model, system=system, prompt=user)
        content = _strip_outer_markdown_fence(response.content)

        attempts_log = list(state.get("attempts_log", []))
        attempts_log.append(
            {
                "content": content,
                "prompt_id": pipeline.repair.prompt,
                "generator_model": validator_model,
                "validation_report": None,
            }
        )
        return {"draft": content, "attempt_number": 2, "repaired": True, "attempts_log": attempts_log}

    async def finalize_node(state: StageGraphState) -> dict[str, Any]:
        if state.get("validation_unavailable"):
            return {"needs_review": True}

        attempts_log = state["attempts_log"]
        if len(attempts_log) == 1:
            winner = attempts_log[0]
        else:
            a1, a2 = attempts_log[0], attempts_log[1]
            s1 = a1["validation_report"]["overall_score"] if a1["validation_report"] else -1
            s2 = a2["validation_report"]["overall_score"] if a2["validation_report"] else -1
            winner = a2 if s2 >= s1 else a1

        report = winner["validation_report"]
        needs_review = report is None or report["overall_score"] < state["threshold"]
        return {"draft": winner["content"], "validation_report": report, "needs_review": needs_review}

    async def gate_node(state: StageGraphState) -> dict[str, Any]:
        if state["mode"] != "stepwise":
            return {}
        # A stage opted into auto-approval skips the human pause once it has
        # actually passed cleanly -- needs_review already encodes "verdict pass
        # and score >= threshold" (see finalize_node), so a stage that needed
        # review still stops here regardless of this flag.
        if stage.auto_approve_on_pass and not state.get("needs_review", True):
            return {}

        resume_value = interrupt(
            {
                "stage_id": stage.id,
                "draft": state["draft"],
                "validation_report": state.get("validation_report"),
                "needs_review": state.get("needs_review", False),
            }
        )
        action = resume_value.get("action") if isinstance(resume_value, dict) else None
        if action == "edit":
            content = resume_value.get("content", state["draft"])
            return {
                "resume_action": resume_value,
                "draft": content,
                "edited_by_user": True,
                "needs_review": False,
            }
        return {"resume_action": resume_value}

    def route_after_gate(state: StageGraphState) -> str:
        if state["mode"] != "stepwise":
            return END
        action = (state.get("resume_action") or {}).get("action")
        return "generate" if action == "regenerate" else END

    graph: StateGraph[StageGraphState] = StateGraph(StageGraphState)
    graph.add_node("generate", generate_node)
    graph.add_node("check_sections", check_sections_node)
    graph.add_node("validate", validate_node)
    graph.add_node("repair", repair_node)
    graph.add_node("finalize", finalize_node)
    graph.add_node("gate", gate_node)

    graph.add_edge(START, "generate")
    graph.add_edge("generate", "check_sections")
    graph.add_conditional_edges(
        "check_sections",
        route_after_check_sections,
        {"validate": "validate", "repair": "repair", "finalize": "finalize"},
    )
    graph.add_conditional_edges(
        "validate", route_after_validate, {"repair": "repair", "finalize": "finalize"}
    )
    graph.add_edge("repair", "check_sections")
    graph.add_edge("finalize", "gate")
    graph.add_conditional_edges("gate", route_after_gate, {"generate": "generate", END: END})

    return graph.compile(checkpointer=checkpointer)


async def is_awaiting_approval(compiled: CompiledStateGraph, config: dict[str, Any]) -> bool:
    return bool((await compiled.aget_state(config)).next)
