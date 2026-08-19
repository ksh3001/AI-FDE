"""Loads and validates config/pipeline.yaml — the authoritative stage declaration.

Adding, reordering, or removing a stage is a config edit here plus a prompt file;
this module is the only place that reads the YAML shape.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from ai_fde.core.prompts.registry import PromptRegistry


class SharedPrompts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system: str
    house_style: str
    validator_system: str


class RepairConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str


class StageConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    order: int = Field(ge=1)
    generator: str
    validator: str
    artifact_filename: str
    generator_variants: dict[str, str] = Field(default_factory=dict)
    default_variant: str | None = None
    #: Stage ids whose artifacts this stage actually needs as context. Empty (the
    #: default) means "every prior artifact" -- today's behaviour, and what every
    #: stage declared before this field existed -- so adding it to a stage is purely
    #: opt-in narrowing, never a behaviour change for stages that don't set it.
    depends_on: list[str] = Field(default_factory=list)
    #: In "stepwise" mode only: skip the human-approval pause when this stage's
    #: result did not need review (validator passed at/above threshold). Has no
    #: effect in "auto" mode, which already never pauses. Defaults to False so a
    #: stage is a mandatory approval gate unless explicitly opted out -- the safe
    #: default for a stage nobody has reviewed yet.
    auto_approve_on_pass: bool = False
    #: Overrides Settings.validator_model for this stage's validator calls only
    #: (generation always uses the configured generator model -- the deliverable
    #: itself is never cheapened). Unset means "use the global default," as today.
    validator_model: str | None = None


class PipelineConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    shared: SharedPrompts
    repair: RepairConfig
    stages: list[StageConfig]

    @model_validator(mode="after")
    def _stage_order_is_unique_and_ascending(self) -> PipelineConfig:
        orders = [s.order for s in self.stages]
        if len(set(orders)) != len(orders):
            raise ValueError("pipeline.yaml stage 'order' values must be unique")
        if orders != sorted(orders):
            raise ValueError("pipeline.yaml stages must be listed in ascending 'order'")
        return self

    @classmethod
    def load(cls, path: Path) -> PipelineConfig:
        if not path.is_file():
            raise FileNotFoundError(f"pipeline config not found: {path}")
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls.model_validate(data)


def validate_pipeline_bindings(pipeline: PipelineConfig, registry: PromptRegistry) -> None:
    """Every prompt id the pipeline references must exist and have the right role.

    Fails loudly at startup — this is what the spec's "if a prompt referenced by
    pipeline.yaml is missing ... stop and tell me" requirement becomes in code.
    """
    errors: list[str] = []

    def _check(prompt_id: str, expected_role: str, where: str) -> None:
        try:
            doc = registry.get(prompt_id)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{where}: {exc}")
            return
        if doc.front_matter.model_role != expected_role:
            errors.append(
                f"{where}: prompt {prompt_id!r} has model_role="
                f"{doc.front_matter.model_role!r}, expected {expected_role!r}"
            )

    _check(pipeline.shared.system, "generator", "shared.system")
    _check(pipeline.shared.house_style, "generator", "shared.house_style")
    _check(pipeline.shared.validator_system, "validator", "shared.validator_system")
    _check(pipeline.repair.prompt, "repair", "repair.prompt")

    for stage in pipeline.stages:
        _check(stage.generator, "generator", f"stage[{stage.id}].generator")
        _check(stage.validator, "validator", f"stage[{stage.id}].validator")
        for variant_name, variant_id in stage.generator_variants.items():
            _check(variant_id, "generator", f"stage[{stage.id}].generator_variants[{variant_name}]")
        if stage.default_variant is not None and stage.default_variant not in stage.generator_variants:
            errors.append(
                f"stage[{stage.id}]: default_variant={stage.default_variant!r} not in generator_variants"
            )

    if errors:
        joined = "\n".join(f"  - {e}" for e in errors)
        raise ValueError(f"pipeline.yaml references prompts that failed validation:\n{joined}")
