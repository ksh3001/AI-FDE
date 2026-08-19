from __future__ import annotations

import json
from pathlib import Path

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from ai_fde.core.models import ParsedDocument
from ai_fde.core.pipeline.config import PipelineConfig
from ai_fde.core.pipeline.graph import build_stage_graph
from ai_fde.core.prompts.composer import build_domain_config
from ai_fde.core.prompts.registry import PromptRegistry
from ai_fde.core.settings import Settings
from tests.helpers import ScriptedLLMClient

USE_CASE = ParsedDocument(
    filename="use_case.md", type="md", page_or_slide_count=1, char_count=10, content="# Use case"
)
THRESHOLD = 80

# This file tests generic generate/validate/repair/gate *mechanics* -- it must not be coupled
# to whatever required_sections real production stages happen to declare (every stage in
# config/pipeline.yaml now declares several; test_required_sections.py owns that behaviour).
# A local, isolated, minimal registry -- generator declares required_sections: [] -- keeps
# check_sections a true no-op here, so ScriptedLLMClient's canned ["# Draft v1", ...] sequences
# are consumed by generate/validate/repair in the order each test actually pins.
_MECHANICS_FRONT_MATTER = {
    "_shared/system.md": """---
id: shared.system
version: 1.0.0
stage: shared
model_role: generator
inputs: []
output_format: markdown
required_sections: []
---
# System

Test system persona.
""",
    "_shared/house_style.md": """---
id: shared.house_style
version: 1.0.0
stage: shared
model_role: generator
inputs: []
output_format: markdown
required_sections: []
---
# House style

Test house style.
""",
    "_shared/validator_system.md": """---
id: shared.validator_system
version: 1.0.0
stage: shared
model_role: validator
inputs: []
output_format: markdown
required_sections: []
---
# Validator persona

Return the JSON schema exactly.
""",
    "stages/test.md": """---
id: stage.test
version: 1.0.0
stage: test
model_role: generator
inputs: [use_case]
output_format: markdown
required_sections: []
---
# Test stage

Produce a draft.
""",
    "validators/test.md": """---
id: validator.test
version: 1.0.0
stage: test
model_role: validator
inputs: [use_case]
output_format: json
required_sections: []
rubric:
  - name: completeness
    weight: 1.0
    description: Placeholder rubric for graph-mechanics tests.
---
# Validate test stage

Score the draft.
""",
    "repair/repair.md": """---
id: repair.test
version: 1.0.0
stage: repair
model_role: repair
inputs: [use_case, evidence, prior_artifacts, original_prompt, failed_draft, validation_report]
output_format: markdown
required_sections: []
---
# Repair pass

## The original brief

{{ original_prompt }}

## The draft that failed validation

{{ failed_draft }}

## Why it failed

{{ validation_report }}
""",
}


@pytest.fixture
def prompt_registry(tmp_path: Path) -> PromptRegistry:
    for rel_path, content in _MECHANICS_FRONT_MATTER.items():
        dest = tmp_path / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
    return PromptRegistry(tmp_path)


@pytest.fixture
def pipeline_config() -> PipelineConfig:
    return PipelineConfig.model_validate(
        {
            "version": 1,
            "shared": {
                "system": "shared.system",
                "house_style": "shared.house_style",
                "validator_system": "shared.validator_system",
            },
            "repair": {"prompt": "repair.test"},
            "stages": [
                {
                    "id": "test",
                    "order": 1,
                    "generator": "stage.test",
                    "validator": "validator.test",
                    "artifact_filename": "test.md",
                }
            ],
        }
    )


def _report(score: int, verdict: str | None = None) -> str:
    return json.dumps(
        {
            "overall_score": score,
            "verdict": verdict or ("pass" if score >= THRESHOLD else "fail"),
            "criteria": [{"name": "completeness", "score": score, "weight": 1.0, "comment": "x"}],
            "issues": [] if score >= THRESHOLD else [
                {"severity": "major", "location": "doc", "problem": "weak", "fix": "improve"}
            ],
            "repair_instructions": "" if score >= THRESHOLD else "improve it",
        }
    )


def _build(
    llm: ScriptedLLMClient,
    prompt_registry: PromptRegistry,
    pipeline_config: PipelineConfig,
    *,
    checkpointer=None,
    stage=None,
):
    stage = stage or pipeline_config.stages[0]  # discovery
    return build_stage_graph(
        llm_client=llm,
        registry=prompt_registry,
        pipeline=pipeline_config,
        stage=stage,
        generator_prompt_id=stage.generator,
        use_case=USE_CASE,
        evidence=[],
        prior_artifacts=[],
        settings=Settings(),
        domain_config=build_domain_config(),
        checkpointer=checkpointer or InMemorySaver(),
    )


def _initial_state(mode: str, *, max_repair_attempts: int = 1) -> dict:
    return {"mode": mode, "threshold": THRESHOLD, "max_repair_attempts": max_repair_attempts}


async def test_pass_first_time_no_repair(prompt_registry, pipeline_config) -> None:
    llm = ScriptedLLMClient(["# Draft v1", _report(90)])
    graph = _build(llm, prompt_registry, pipeline_config)
    config = {"configurable": {"thread_id": "t-pass"}}

    result = await graph.ainvoke(_initial_state("auto"), config=config)

    assert result["draft"] == "# Draft v1"
    assert result["validation_report"]["overall_score"] == 90
    assert result["needs_review"] is False
    assert result["repaired"] is False
    assert len(llm.calls) == 2  # generate, validate -- no repair


async def test_fail_then_pass_after_repair(prompt_registry, pipeline_config) -> None:
    llm = ScriptedLLMClient(["# Draft v1", _report(60), "# Draft v2 (repaired)", _report(90)])
    graph = _build(llm, prompt_registry, pipeline_config)
    config = {"configurable": {"thread_id": "t-repair-pass"}}

    result = await graph.ainvoke(_initial_state("auto"), config=config)

    assert result["draft"] == "# Draft v2 (repaired)"
    assert result["validation_report"]["overall_score"] == 90
    assert result["needs_review"] is False
    assert result["repaired"] is True
    assert len(llm.calls) == 4


async def test_fail_twice_marks_needs_review_and_keeps_better_draft(
    prompt_registry, pipeline_config
) -> None:
    # Repaired draft scores lower than the original -- the higher-scoring draft
    # (the original, attempt 1) must win, per "accept the higher-scoring of the two".
    llm = ScriptedLLMClient(["# Draft v1", _report(70), "# Draft v2 (repaired)", _report(60)])
    graph = _build(llm, prompt_registry, pipeline_config)
    config = {"configurable": {"thread_id": "t-fail-twice"}}

    result = await graph.ainvoke(_initial_state("auto"), config=config)

    assert result["draft"] == "# Draft v1"
    assert result["validation_report"]["overall_score"] == 70
    assert result["needs_review"] is True
    assert result["repaired"] is True
    assert len(llm.calls) == 4


async def test_max_repair_attempts_zero_skips_repair_entirely(prompt_registry, pipeline_config) -> None:
    """MAX_REPAIR_ATTEMPTS=0 (env-driven) accepts a failing draft as-is instead of
    spending a second generator call on it -- the repair node itself is untouched,
    only routing changes."""
    llm = ScriptedLLMClient(["# Draft v1", _report(10)])
    graph = _build(llm, prompt_registry, pipeline_config)
    config = {"configurable": {"thread_id": "t-repair-disabled"}}

    result = await graph.ainvoke(_initial_state("auto", max_repair_attempts=0), config=config)

    assert result["draft"] == "# Draft v1"
    assert result["validation_report"]["overall_score"] == 10
    assert result["needs_review"] is True
    assert result["repaired"] is False
    assert len(llm.calls) == 2  # generate, validate -- no repair call at all


async def test_repair_runs_at_most_once_ever(prompt_registry, pipeline_config) -> None:
    """Pinned per the build spec: 'the rule most likely to regress'. Even when the
    repaired draft is still badly below threshold, there must be no second repair."""
    llm = ScriptedLLMClient(["# Draft v1", _report(10), "# Draft v2 (repaired)", _report(10)])
    graph = _build(llm, prompt_registry, pipeline_config)
    config = {"configurable": {"thread_id": "t-repair-once"}}

    result = await graph.ainvoke(_initial_state("auto"), config=config)

    assert result["needs_review"] is True
    assert result["repaired"] is True
    assert len(llm.calls) == 4  # generate, validate, repair, validate -- and stop


async def test_validator_model_override_is_used_for_validate_and_repair_calls(
    prompt_registry, pipeline_config
) -> None:
    stage = pipeline_config.stages[0].model_copy(update={"validator_model": "cheap-tier-model"})
    llm = ScriptedLLMClient(["# Draft v1", _report(60), "# Draft v2 (repaired)", _report(90)])
    graph = _build(llm, prompt_registry, pipeline_config, stage=stage)
    config = {"configurable": {"thread_id": "t-validator-model-override"}}

    await graph.ainvoke(_initial_state("auto"), config=config)

    generate_call, validate_call, repair_call, revalidate_call = llm.calls
    assert generate_call["model"] == Settings().generator_model  # generation is never cheapened
    assert validate_call["model"] == "cheap-tier-model"
    assert repair_call["model"] == "cheap-tier-model"
    assert revalidate_call["model"] == "cheap-tier-model"


async def test_malformed_validator_json_recovers_on_retry(prompt_registry, pipeline_config) -> None:
    llm = ScriptedLLMClient(["# Draft v1", "not json at all", _report(91)])
    graph = _build(llm, prompt_registry, pipeline_config)
    config = {"configurable": {"thread_id": "t-malformed-recover"}}

    result = await graph.ainvoke(_initial_state("auto"), config=config)

    assert result["validation_unavailable"] is False
    assert result["validation_report"]["overall_score"] == 91
    assert len(llm.calls) == 3  # generate, validate (bad), validate retry (good)


async def test_malformed_validator_json_twice_marks_validation_unavailable(
    prompt_registry, pipeline_config
) -> None:
    llm = ScriptedLLMClient(["# Draft v1", "not json", "still not json"])
    graph = _build(llm, prompt_registry, pipeline_config)
    config = {"configurable": {"thread_id": "t-malformed-twice"}}

    result = await graph.ainvoke(_initial_state("auto"), config=config)

    assert result["validation_unavailable"] is True
    assert result["needs_review"] is True
    assert len(llm.calls) == 3  # generate, validate, validate retry -- no repair attempted


async def test_stepwise_mode_pauses_at_gate_then_resumes_on_approve(
    prompt_registry, pipeline_config
) -> None:
    llm = ScriptedLLMClient(["# Draft v1", _report(90)])
    graph = _build(llm, prompt_registry, pipeline_config)
    config = {"configurable": {"thread_id": "t-stepwise-approve"}}

    first = await graph.ainvoke(_initial_state("stepwise"), config=config)
    assert "__interrupt__" in first
    assert bool(graph.get_state(config).next) is True

    final = await graph.ainvoke(Command(resume={"action": "approve"}), config=config)

    assert final["draft"] == "# Draft v1"
    assert final["needs_review"] is False
    assert len(llm.calls) == 2  # approving does not trigger any further LLM calls
    assert graph.get_state(config).next == ()


async def test_stepwise_edit_overrides_draft_without_revalidation(
    prompt_registry, pipeline_config
) -> None:
    llm = ScriptedLLMClient(["# Draft v1", _report(90)])
    graph = _build(llm, prompt_registry, pipeline_config)
    config = {"configurable": {"thread_id": "t-stepwise-edit"}}

    await graph.ainvoke(_initial_state("stepwise"), config=config)
    final = await graph.ainvoke(
        Command(resume={"action": "edit", "content": "# User-edited artifact"}), config=config
    )

    assert final["draft"] == "# User-edited artifact"
    assert final["needs_review"] is False
    assert len(llm.calls) == 2  # editing does not trigger any further LLM calls


async def test_stepwise_regenerate_loops_back_with_steering_note(
    prompt_registry, pipeline_config
) -> None:
    llm = ScriptedLLMClient(["# Draft v1", _report(90), "# Draft v2", _report(95)])
    graph = _build(llm, prompt_registry, pipeline_config)
    config = {"configurable": {"thread_id": "t-stepwise-regenerate"}}

    await graph.ainvoke(_initial_state("stepwise"), config=config)
    second = await graph.ainvoke(
        Command(resume={"action": "regenerate", "note": "be more specific about identifiers"}),
        config=config,
    )
    assert "__interrupt__" in second  # paused again after the regenerated draft
    assert "be more specific about identifiers" in llm.calls[2]["prompt"]

    final = await graph.ainvoke(Command(resume={"action": "approve"}), config=config)

    assert final["draft"] == "# Draft v2"
    assert final["regenerate_count"] == 1
    assert len(llm.calls) == 4
