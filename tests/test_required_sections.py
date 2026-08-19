"""I1: deterministic `required_sections` enforcement (graph.py's `check_sections` node).

Every real prompt on disk currently declares `required_sections: []`, so test_graph.py's
suite exercises this node only as a no-op pass-through. These tests build a small,
self-contained prompt library (via tmp_path) with one stage that actually declares a
required section, to pin the enforcement behaviour itself: a missing section must route
straight to repair without spending a validator call, and the "no validator call" property
must hold whether or not repair recovers it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from ai_fde.core.models import ParsedDocument
from ai_fde.core.pipeline.config import PipelineConfig
from ai_fde.core.pipeline.graph import _find_missing_sections, build_stage_graph
from ai_fde.core.prompts.composer import build_domain_config
from ai_fde.core.prompts.registry import PromptRegistry
from ai_fde.core.settings import Settings
from tests.helpers import ScriptedLLMClient

USE_CASE = ParsedDocument(
    filename="use_case.md", type="md", page_or_slide_count=1, char_count=10, content="# Use case"
)
THRESHOLD = 80

_FRONT_MATTER_SHARED_GENERATOR = """---
id: {id}
version: 1.0.0
stage: shared
model_role: generator
inputs: []
output_format: markdown
required_sections: []
---
# {id}

Test fragment.
"""

_SHARED_VALIDATOR_SYSTEM = """---
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
"""

_STAGE_GENERATOR = """---
id: stage.test
version: 1.0.0
stage: test
model_role: generator
inputs: [use_case]
output_format: markdown
required_sections: ["Findings"]
---
# Test stage

Produce a `## Findings` section with real content.
"""

_STAGE_VALIDATOR = """---
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
    description: Has a Findings section with real content.
---
# Validate test stage

Score the draft.
"""

_REPAIR_PROMPT = """---
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
"""


@pytest.fixture
def small_registry(tmp_path: Path) -> PromptRegistry:
    (tmp_path / "_shared").mkdir()
    (tmp_path / "_shared" / "system.md").write_text(
        _FRONT_MATTER_SHARED_GENERATOR.format(id="shared.system"), encoding="utf-8"
    )
    (tmp_path / "_shared" / "house_style.md").write_text(
        _FRONT_MATTER_SHARED_GENERATOR.format(id="shared.house_style"), encoding="utf-8"
    )
    (tmp_path / "_shared" / "validator_system.md").write_text(_SHARED_VALIDATOR_SYSTEM, encoding="utf-8")

    (tmp_path / "stages").mkdir()
    (tmp_path / "stages" / "test.md").write_text(_STAGE_GENERATOR, encoding="utf-8")

    (tmp_path / "validators").mkdir()
    (tmp_path / "validators" / "test.md").write_text(_STAGE_VALIDATOR, encoding="utf-8")

    (tmp_path / "repair").mkdir()
    (tmp_path / "repair" / "repair.md").write_text(_REPAIR_PROMPT, encoding="utf-8")

    return PromptRegistry(tmp_path)


@pytest.fixture
def small_pipeline_config() -> PipelineConfig:
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


def _report(score: int) -> str:
    return json.dumps(
        {
            "overall_score": score,
            "verdict": "pass" if score >= THRESHOLD else "fail",
            "criteria": [{"name": "completeness", "score": score, "weight": 1.0, "comment": "x"}],
            "issues": [],
            "repair_instructions": "",
        }
    )


def _build(llm: ScriptedLLMClient, registry: PromptRegistry, pipeline_config: PipelineConfig):
    stage = pipeline_config.stages[0]
    return build_stage_graph(
        llm_client=llm,
        registry=registry,
        pipeline=pipeline_config,
        stage=stage,
        generator_prompt_id=stage.generator,
        use_case=USE_CASE,
        evidence=[],
        prior_artifacts=[],
        settings=Settings(),
        domain_config=build_domain_config(),
        checkpointer=InMemorySaver(),
    )


def _initial_state(*, max_repair_attempts: int = 1) -> dict:
    return {"mode": "auto", "threshold": THRESHOLD, "max_repair_attempts": max_repair_attempts}


# -- unit tests for the heading scan -----------------------------------------------------


def test_find_missing_sections_is_case_insensitive_and_ignores_trailing_whitespace() -> None:
    draft = "# Title\n\n##   findings   \n\ncontent\n"
    assert _find_missing_sections(draft, ["Findings"]) == []


def test_find_missing_sections_does_not_match_h3() -> None:
    draft = "# Title\n\n### Findings\n\ncontent\n"
    assert _find_missing_sections(draft, ["Findings"]) == ["Findings"]


def test_find_missing_sections_reports_every_gap_in_declared_order() -> None:
    draft = "# Title\n\n## Findings\n\ncontent\n"
    assert _find_missing_sections(draft, ["Findings", "Open questions", "Risks"]) == [
        "Open questions",
        "Risks",
    ]


# -- graph-level behaviour ----------------------------------------------------------------


async def test_present_section_flows_through_unaffected(small_registry, small_pipeline_config) -> None:
    llm = ScriptedLLMClient(["# Draft\n\n## Findings\n\nreal content", _report(90)])
    graph = _build(llm, small_registry, small_pipeline_config)
    config = {"configurable": {"thread_id": "t-present"}}

    result = await graph.ainvoke(_initial_state(), config=config)

    assert result["needs_review"] is False
    assert result["repaired"] is False
    assert len(llm.calls) == 2  # generate, validate -- check_sections spent no call


async def test_missing_section_skips_the_validator_call_and_goes_straight_to_repair(
    small_registry, small_pipeline_config
) -> None:
    llm = ScriptedLLMClient(
        [
            "# Draft with no Findings section",
            "# Repaired draft\n\n## Findings\n\nnow present",
            _report(90),
        ]
    )
    graph = _build(llm, small_registry, small_pipeline_config)
    config = {"configurable": {"thread_id": "t-missing-then-fixed"}}

    result = await graph.ainvoke(_initial_state(), config=config)

    assert len(llm.calls) == 3  # generate, repair, validate -- NOT generate, validate, repair, validate
    assert result["draft"] == "# Repaired draft\n\n## Findings\n\nnow present"
    assert result["repaired"] is True
    assert result["needs_review"] is False
    assert result["validation_report"]["overall_score"] == 90


async def test_missing_section_still_missing_after_repair_marks_needs_review_with_no_validator_call(
    small_registry, small_pipeline_config
) -> None:
    llm = ScriptedLLMClient(
        ["# Draft v1, no Findings", "# Draft v2, still no Findings"]
    )
    graph = _build(llm, small_registry, small_pipeline_config)
    config = {"configurable": {"thread_id": "t-missing-twice"}}

    result = await graph.ainvoke(_initial_state(), config=config)

    assert len(llm.calls) == 2  # generate, repair -- the validator is never called
    assert result["needs_review"] is True
    assert result["repaired"] is True
    assert result["validation_report"]["overall_score"] == 0
    assert result["validation_report"]["verdict"] == "fail"
    assert "Findings" in result["validation_report"]["issues"][0]["problem"]


async def test_missing_section_with_repair_disabled_skips_repair_and_validate_entirely(
    small_registry, small_pipeline_config
) -> None:
    llm = ScriptedLLMClient(["# Draft with no Findings section"])
    graph = _build(llm, small_registry, small_pipeline_config)
    config = {"configurable": {"thread_id": "t-missing-no-repair-budget"}}

    result = await graph.ainvoke(_initial_state(max_repair_attempts=0), config=config)

    assert len(llm.calls) == 1  # generate only -- no repair, no validator call
    assert result["needs_review"] is True
    assert result["repaired"] is False
    assert result["validation_report"]["overall_score"] == 0
