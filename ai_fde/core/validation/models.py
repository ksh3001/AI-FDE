"""Validator-model JSON output contract.

This is the one place the spec is explicit about strictness: "Parse into a Pydantic
strict model. On parse failure, retry the validator once with the schema error fed
back; if it fails again, mark the stage validation_unavailable." These models are
that parse target.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Severity = Literal["critical", "major", "minor"]
Verdict = Literal["pass", "fail"]


class CriterionScore(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    name: str
    score: int = Field(ge=0, le=100)
    weight: float = Field(gt=0, le=1)
    comment: str


class ValidationIssue(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    severity: Severity
    location: str
    problem: str
    fix: str


class ValidationReport(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    overall_score: int = Field(ge=0, le=100)
    verdict: Verdict
    criteria: list[CriterionScore]
    issues: list[ValidationIssue] = Field(default_factory=list)
    repair_instructions: str = ""

    @model_validator(mode="after")
    def _at_least_one_criterion(self) -> ValidationReport:
        if not self.criteria:
            raise ValueError("validation report must include at least one scored criterion")
        return self
