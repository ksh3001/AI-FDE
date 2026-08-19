from __future__ import annotations

import json

from ai_fde.adapters.llm.fake import FakeLLMClient
from ai_fde.core.models import ParsedDocument
from ai_fde.core.pipeline.config import PipelineConfig
from ai_fde.core.prompts.composer import (
    GENERATION_CONTEXT_SENTINEL,
    compose_generation_prompt,
    compose_validation_prompt,
)
from ai_fde.core.prompts.registry import PromptRegistry
from ai_fde.core.validation.models import ValidationReport

USE_CASE = ParsedDocument(
    filename="use_case.md", type="md", page_or_slide_count=1, char_count=10, content="# Use case"
)


async def test_fake_llm_generates_markdown_for_a_stage(
    prompt_registry: PromptRegistry, pipeline_config: PipelineConfig
) -> None:
    system, user = compose_generation_prompt(
        registry=prompt_registry,
        pipeline=pipeline_config,
        generator_prompt_id="stage.discovery",
        use_case=USE_CASE,
        evidence=[],
        prior_artifacts=[],
    )
    response = await FakeLLMClient().complete(model="gpt-4.1", system=system, prompt=user)
    assert "Discovery" in response.content
    assert "use_case.md" in response.content


def test_generation_prompt_puts_run_context_before_stage_instructions(
    prompt_registry: PromptRegistry, pipeline_config: PipelineConfig
) -> None:
    """I3/Phase 3 prefix-caching reorder: use_case/evidence/prior_artifacts (stable
    across every stage of a run) must come before the stage-specific instructions
    (the only part that changes per stage), so the shared block forms a cacheable
    prefix. See composer.py's GENERATION_CONTEXT_SENTINEL docstring."""
    _, user = compose_generation_prompt(
        registry=prompt_registry,
        pipeline=pipeline_config,
        generator_prompt_id="stage.discovery",
        use_case=USE_CASE,
        evidence=[],
        prior_artifacts=[],
    )
    assert user.startswith("## Use case")
    assert GENERATION_CONTEXT_SENTINEL in user
    context_part, stage_part = user.split(GENERATION_CONTEXT_SENTINEL, 1)
    assert "## Prior artifacts" in context_part
    assert "Prompt 01" in stage_part  # stage.discovery's own heading text


def test_validation_prompt_actually_includes_the_rubric_it_refers_to(
    prompt_registry: PromptRegistry, pipeline_config: PipelineConfig
) -> None:
    """Regression test: validator bodies say 'score against the rubric above', but
    front-matter rubric: is never otherwise rendered into what the model sees --
    this caused a real validator to invent its own JSON shape against a live
    Azure deployment. The rubric's criterion names must actually appear."""
    _, user = compose_validation_prompt(
        registry=prompt_registry,
        pipeline=pipeline_config,
        validator_prompt_id="validator.scqa",
        use_case=USE_CASE,
        evidence=[],
        prior_artifacts=[],
        draft="# SCQA\n\nSome draft.",
    )
    rubric = prompt_registry.get("validator.scqa").front_matter.rubric
    assert rubric
    for criterion in rubric:
        assert criterion.name in user
        assert str(criterion.weight) in user


async def test_fake_llm_generates_parseable_validation_report(
    prompt_registry: PromptRegistry, pipeline_config: PipelineConfig
) -> None:
    system, user = compose_validation_prompt(
        registry=prompt_registry,
        pipeline=pipeline_config,
        validator_prompt_id="validator.discovery",
        use_case=USE_CASE,
        evidence=[],
        prior_artifacts=[],
        draft="# Discovery\n\nSome content.",
    )
    response = await FakeLLMClient(validator_score=92).complete(
        model="gpt-5.1", system=system, prompt=user
    )
    report = ValidationReport.model_validate(json.loads(response.content))
    assert report.overall_score == 92
    assert report.verdict == "pass"
    assert sum(c.weight for c in report.criteria) == 1.0


async def test_fake_llm_below_threshold_report_has_issues(
    prompt_registry: PromptRegistry, pipeline_config: PipelineConfig
) -> None:
    system, user = compose_validation_prompt(
        registry=prompt_registry,
        pipeline=pipeline_config,
        validator_prompt_id="validator.scqa",
        use_case=USE_CASE,
        evidence=[],
        prior_artifacts=[],
        draft="# SCQA\n\nWeak draft.",
    )
    response = await FakeLLMClient(validator_score=55).complete(
        model="gpt-5.1", system=system, prompt=user
    )
    report = ValidationReport.model_validate(json.loads(response.content))
    assert report.verdict == "fail"
    assert report.issues
    assert report.repair_instructions
