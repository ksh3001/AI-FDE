from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from ai_fde.core.pipeline.config import PipelineConfig, validate_pipeline_bindings
from ai_fde.core.prompts.models import PromptFrontMatter
from ai_fde.core.prompts.registry import PromptLoadError, PromptRegistry


def test_registry_loads_the_real_prompt_library(prompt_registry: PromptRegistry) -> None:
    ids = {doc.front_matter.id for doc in prompt_registry.list_all()}
    assert "stage.discovery" in ids
    assert "stage.decisions" in ids
    assert "validator.decisions" in ids
    assert "repair.default" in ids


def test_every_pipeline_stage_has_a_generator_and_validator_prompt(
    prompt_registry: PromptRegistry, pipeline_config: PipelineConfig
) -> None:
    for stage in pipeline_config.stages:
        generator = prompt_registry.get(stage.generator)
        assert generator.front_matter.model_role == "generator"

        validator = prompt_registry.get(stage.validator)
        assert validator.front_matter.model_role == "validator"

        for variant_id in stage.generator_variants.values():
            variant_doc = prompt_registry.get(variant_id)
            assert variant_doc.front_matter.model_role == "generator"


def test_validate_pipeline_bindings_passes_for_the_real_config(
    prompt_registry: PromptRegistry, pipeline_config: PipelineConfig
) -> None:
    validate_pipeline_bindings(pipeline_config, prompt_registry)  # must not raise


def test_every_validator_rubric_weights_sum_to_one(prompt_registry: PromptRegistry) -> None:
    # Per-stage validators (stage != "shared") must declare a rubric that sums to
    # 1.0; shared.validator_system is a persona fragment, not a stage validator,
    # and is exempt (see PromptFrontMatter._rubric_only_on_validators).
    validators = [
        d
        for d in prompt_registry.list_all()
        if d.front_matter.model_role == "validator" and d.front_matter.stage != "shared"
    ]
    assert validators, "expected at least one per-stage validator prompt to be loaded"

    for doc in validators:
        assert doc.front_matter.rubric is not None
        total = sum(c.weight for c in doc.front_matter.rubric)
        assert total == pytest.approx(1.0, abs=1e-6), (
            f"{doc.front_matter.id} rubric weights sum to {total}, not 1.0"
        )


def test_non_validator_prompts_declare_no_rubric(prompt_registry: PromptRegistry) -> None:
    for doc in prompt_registry.list_all():
        if doc.front_matter.model_role != "validator":
            assert doc.front_matter.rubric is None


def test_stage_prompt_ids_are_unique(prompt_registry: PromptRegistry) -> None:
    ids = [doc.front_matter.id for doc in prompt_registry.list_all()]
    assert len(ids) == len(set(ids))


def test_validator_front_matter_rejects_rubric_not_summing_to_one() -> None:
    with pytest.raises(ValueError, match="sum to 1.0"):
        PromptFrontMatter.model_validate(
            {
                "id": "validator.broken",
                "version": "1.0.0",
                "stage": "discovery",
                "model_role": "validator",
                "output_format": "json",
                "rubric": [
                    {"name": "a", "weight": 0.5, "description": "..."},
                    {"name": "b", "weight": 0.6, "description": "..."},
                ],
            }
        )


def test_generator_front_matter_rejects_a_rubric() -> None:
    with pytest.raises(ValueError, match="only validator prompts"):
        PromptFrontMatter.model_validate(
            {
                "id": "stage.broken",
                "version": "1.0.0",
                "stage": "discovery",
                "model_role": "generator",
                "output_format": "markdown",
                "rubric": [{"name": "a", "weight": 1.0, "description": "..."}],
            }
        )


def test_registry_fails_loudly_on_missing_front_matter(tmp_path: Path) -> None:
    stages_dir = tmp_path / "stages"
    stages_dir.mkdir()
    (stages_dir / "bad.md").write_text("# No front matter here\n", encoding="utf-8")
    with pytest.raises(PromptLoadError, match="front-matter"):
        PromptRegistry(tmp_path)


def test_registry_fails_loudly_on_invalid_yaml(tmp_path: Path) -> None:
    stages_dir = tmp_path / "stages"
    stages_dir.mkdir()
    (stages_dir / "bad.md").write_text(
        "---\nid: [unterminated\n---\nbody\n", encoding="utf-8"
    )
    with pytest.raises(PromptLoadError, match="failed to load prompt library"):
        PromptRegistry(tmp_path)


def test_registry_fails_loudly_on_missing_directory(tmp_path: Path) -> None:
    with pytest.raises(PromptLoadError, match="not found"):
        PromptRegistry(tmp_path / "does-not-exist")


def test_registry_fails_loudly_on_duplicate_ids(tmp_path: Path) -> None:
    stages_dir = tmp_path / "stages"
    stages_dir.mkdir()
    front_matter = {
        "id": "stage.dup",
        "version": "1.0.0",
        "stage": "discovery",
        "model_role": "generator",
        "output_format": "markdown",
    }
    for name in ("a.md", "b.md"):
        (stages_dir / name).write_text(
            "---\n" + yaml.safe_dump(front_matter) + "---\nbody\n", encoding="utf-8"
        )
    with pytest.raises(PromptLoadError, match="duplicate prompt id"):
        PromptRegistry(tmp_path)


def test_pipeline_rejects_a_reference_to_a_missing_prompt(
    tmp_path: Path, prompt_registry: PromptRegistry
) -> None:
    config = PipelineConfig.model_validate(
        {
            "version": 1,
            "shared": {
                "system": "shared.system",
                "house_style": "shared.house_style",
                "validator_system": "shared.validator_system",
            },
            "repair": {"prompt": "repair.default"},
            "stages": [
                {
                    "id": "discovery",
                    "order": 1,
                    "generator": "stage.does_not_exist",
                    "validator": "validator.discovery",
                    "artifact_filename": "01-discovery.md",
                }
            ],
        }
    )
    with pytest.raises(ValueError, match="stage\\[discovery\\].generator"):
        validate_pipeline_bindings(config, prompt_registry)


def test_render_substitutes_domain_placeholders_without_touching_other_braces(
    prompt_registry: PromptRegistry,
) -> None:
    # stage.risk_classification is the one stage prompt that actually references a
    # domain token ({SYSTEM}) in its body; stage.discovery no longer does (v2 rewrite).
    rendered = prompt_registry.render(
        "stage.risk_classification",
        domain_config={"SYSTEM": "the maritime maintenance advisory system"},
    )
    assert "the maritime maintenance advisory system" in rendered
    assert "{SYSTEM}" not in rendered


def test_render_jinja_context_fills_repair_prompt(prompt_registry: PromptRegistry) -> None:
    rendered = prompt_registry.render(
        "repair.default",
        jinja_context={
            "original_prompt": "ORIGINAL",
            "failed_draft": "DRAFT",
            "validation_report": "REPORT",
        },
    )
    assert "ORIGINAL" in rendered
    assert "DRAFT" in rendered
    assert "REPORT" in rendered
    assert "{{" not in rendered
