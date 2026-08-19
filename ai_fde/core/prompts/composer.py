"""Composes the full LLM call from shared fragments, a stage prompt, and run context.

The original prompt bodies never contain `{{ use_case }}`-style placeholders for
use_case/evidence/prior_artifacts (only the newly-authored repair prompt uses
Jinja2 for its own inputs) -- so composition, not in-body substitution, is how
"each stage receives the parsed use case, the evidence context, and the
accepted artifacts of all prior stages" is actually satisfied here.

Every compose_* function returns a (system, user) pair matching LLMClient.complete's
(system, prompt) signature -- never one merged blob.
"""

from __future__ import annotations

from ai_fde.core.models import ParsedDocument, StageArtifact
from ai_fde.core.pipeline.config import PipelineConfig
from ai_fde.core.prompts.models import RubricCriterion
from ai_fde.core.prompts.registry import PromptRegistry

#: AI_FDE resolves the raw library's domain placeholders from run config, not by
#: hand-editing case-study/*.md files per run. Callers may override any subset;
#: unset placeholders fall back to an advisory-safe generic default that steers
#: the model to ask rather than assume.
DEFAULT_DOMAIN_CONFIG: dict[str, str] = {
    "DOMAIN": "the business domain described in the uploaded use case",
    "SYSTEM": "the advisory system being scoped in this run",
    "DECISION_PROBLEM": "the decision or engineering question described in the uploaded use case",
    "ROLES": "the roles named in the use case and evidence documents",
    "AUTHORITY_MATRIX": (
        "not separately supplied for this run -- infer accountable human roles from the use "
        "case and evidence, and surface any authority question you cannot resolve as an open "
        "question rather than assuming who may decide"
    ),
    "SOURCE_SYSTEMS": "the systems named in the use case and evidence documents",
    "DATA_DICTIONARY": (
        "not separately supplied for this run -- infer field meanings from the use case and "
        "evidence, and flag ambiguous fields as open questions rather than guessing"
    ),
    "PROHIBITED_ACTIONS": (
        "executing, approving, or dispatching any operational action; declaring any entity fit, "
        "unfit, compliant, or non-compliant; writing to any operational or control system"
    ),
    "PRIORITY_RULE": (
        "safety, environmental, security, and statutory/compliance authority are never "
        "overridden by commercial urgency or convenience"
    ),
}


def build_domain_config(overrides: dict[str, str] | None = None) -> dict[str, str]:
    config = dict(DEFAULT_DOMAIN_CONFIG)
    if overrides:
        config.update(overrides)
    return config


def _format_document(doc: ParsedDocument) -> str:
    return f"### {doc.filename} ({doc.type}, {doc.char_count} chars)\n\n{doc.content}"


def _evidence_block(evidence: list[ParsedDocument]) -> str:
    if not evidence:
        return "(no evidence documents were supplied for this run)"
    return "\n\n".join(_format_document(doc) for doc in evidence)


def _prior_artifacts_block(prior_artifacts: list[StageArtifact]) -> str:
    if not prior_artifacts:
        return "(this is the first stage; no prior artifacts exist yet)"
    return "\n\n".join(
        f"### Stage: {a.stage_id} (score {a.score}/100)\n\n{a.content}" for a in prior_artifacts
    )


#: Separates the run-context block (use case / evidence / prior artifacts -- stable
#: across every stage in a run) from the stage-specific instructions in a generation
#: prompt's user message, with context first so it forms a cacheable prefix (see
#: compose_generation_prompt). A literal "---" horizontal rule won't do: uploaded
#: use-case/evidence documents are arbitrary user markdown and may legitimately
#: contain one. This sentinel is deliberately something no real document or stage
#: prompt would produce by coincidence.
GENERATION_CONTEXT_SENTINEL = "\n\n<!-- ai_fde:stage-instructions -->\n\n"


def _rubric_block(rubric: list[RubricCriterion]) -> str:
    """Front-matter `rubric:` is never otherwise rendered into the prompt sent to
    the model -- without this, a validator body saying "score against the rubric
    above" refers to something the model literally cannot see, and it improvises
    its own criterion names/shape instead of the ones the pipeline expects back."""
    lines = ["## Rubric (score each criterion by exactly this name; weights sum to 1.0)", ""]
    for c in rubric:
        lines.append(f"- **{c.name}** (weight {c.weight}): {c.description}")
    return "\n".join(lines)


def compose_generation_prompt(
    *,
    registry: PromptRegistry,
    pipeline: PipelineConfig,
    generator_prompt_id: str,
    use_case: ParsedDocument,
    evidence: list[ParsedDocument],
    prior_artifacts: list[StageArtifact],
    domain_config: dict[str, str] | None = None,
) -> tuple[str, str]:
    domain_config = domain_config or build_domain_config()

    system = registry.render(pipeline.shared.system, domain_config=domain_config)
    house_style = registry.render(pipeline.shared.house_style, domain_config=domain_config)
    stage_body = registry.render(generator_prompt_id, domain_config=domain_config)

    system_message = f"{system}\n\n{house_style}"
    # Run context first, stage instructions last: use_case/evidence are byte-identical
    # across every stage of a run (and prior_artifacts identical up to the point they
    # accumulate), so this ordering lets provider-side prompt caching credit that
    # shared prefix across stages -- placing the ever-changing, stage-specific body
    # first (as this used to) defeated that entirely. See GENERATION_CONTEXT_SENTINEL.
    user_message = (
        f"## Use case\n\n{_format_document(use_case)}\n\n"
        f"## Evidence\n\n{_evidence_block(evidence)}\n\n"
        f"## Prior artifacts\n\n{_prior_artifacts_block(prior_artifacts)}"
        f"{GENERATION_CONTEXT_SENTINEL}{stage_body}\n"
    )
    return system_message, user_message


def compose_validation_prompt(
    *,
    registry: PromptRegistry,
    pipeline: PipelineConfig,
    validator_prompt_id: str,
    use_case: ParsedDocument,
    evidence: list[ParsedDocument],
    prior_artifacts: list[StageArtifact],
    draft: str,
    domain_config: dict[str, str] | None = None,
) -> tuple[str, str]:
    domain_config = domain_config or build_domain_config()

    validator_system = registry.render(
        pipeline.shared.validator_system, domain_config=domain_config
    )
    validator_body = registry.render(validator_prompt_id, domain_config=domain_config)
    rubric = registry.get(validator_prompt_id).front_matter.rubric
    assert rubric, f"{validator_prompt_id} is a validator prompt but declares no rubric"

    user_message = (
        f"{validator_body}\n\n{_rubric_block(rubric)}\n\n---\n\n"
        f"## Use case\n\n{_format_document(use_case)}\n\n"
        f"## Evidence\n\n{_evidence_block(evidence)}\n\n"
        f"## Prior artifacts\n\n{_prior_artifacts_block(prior_artifacts)}\n\n"
        f"## Draft to score\n\n{draft}\n"
    )
    return validator_system, user_message


def compose_repair_prompt(
    *,
    registry: PromptRegistry,
    pipeline: PipelineConfig,
    original_prompt: str,
    failed_draft: str,
    validation_report_json: str,
    domain_config: dict[str, str] | None = None,
) -> tuple[str, str]:
    domain_config = domain_config or build_domain_config()

    # Repair is generated by the validator model acting as generator (per the
    # spec's generate -> validate -> repair loop), so it inherits the
    # validator's persona as its system message.
    system_message = registry.render(
        pipeline.shared.validator_system, domain_config=domain_config
    )
    user_message = registry.render(
        pipeline.repair.prompt,
        jinja_context={
            "original_prompt": original_prompt,
            "failed_draft": failed_draft,
            "validation_report": validation_report_json,
        },
    )
    return system_message, user_message
