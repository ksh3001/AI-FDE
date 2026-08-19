"""Front-matter schema every prompt file on disk must satisfy.

Validated at PromptRegistry load time — never at request time, per the build spec's
"fail loudly at startup" requirement.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ModelRole = Literal["generator", "validator", "repair"]
OutputFormat = Literal["markdown", "json"]

_WEIGHT_SUM_TOLERANCE = 1e-6


class RubricCriterion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    weight: float = Field(gt=0, le=1)
    description: str


class PromptFrontMatter(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    version: str
    stage: str
    model_role: ModelRole
    inputs: list[str] = Field(default_factory=list)
    output_format: OutputFormat
    required_sections: list[str] = Field(default_factory=list)
    rubric: list[RubricCriterion] | None = None

    @model_validator(mode="after")
    def _rubric_only_on_validators(self) -> PromptFrontMatter:
        # `stage: shared` covers prompts/_shared/*.md — persona/style fragments that
        # are composed into other prompts rather than run standalone against an LLM,
        # so validator_system.md (model_role=validator, the shared scoring
        # philosophy) is exempt from needing its own per-criterion rubric.
        if self.model_role == "validator" and self.stage != "shared":
            if not self.rubric:
                raise ValueError("validator prompts must declare a non-empty rubric")
            total = sum(c.weight for c in self.rubric)
            if abs(total - 1.0) > _WEIGHT_SUM_TOLERANCE:
                raise ValueError(f"rubric weights must sum to 1.0, got {total:.4f}")
        elif self.rubric is not None and self.model_role != "validator":
            raise ValueError(
                f"only validator prompts may declare a rubric (model_role={self.model_role!r})"
            )
        return self
