"""Explicit request AND response models for every route — never a bare dict."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ai_fde.core.pipeline.state import RunMode, RunStatus
from ai_fde.core.prompts.models import ModelRole, OutputFormat


class PromptSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str | None
    version: str
    stage: str
    model_role: ModelRole
    output_format: OutputFormat


class PromptLibraryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompts: list[PromptSummary]


class PromptDetail(PromptSummary):
    body: str


class RunCreateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    status: Literal["queued"] = "queued"


class StageArtifactSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage_id: str
    score: int
    verdict: Literal["pass", "fail"]
    needs_review: bool
    validation_unavailable: bool
    created_at: datetime


class RunSummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    status: RunStatus
    mode: RunMode
    current_stage: str | None
    failed_stage: str | None
    failure_reason: str | None
    created_at: datetime
    stage_ids: list[str]
    stages: list[StageArtifactSummary]


class AttemptSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attempt_number: int
    content: str
    prompt_id: str
    prompt_version: str
    generator_model: str
    validation_report: dict[str, Any] | None


class StageArtifactResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage_id: str
    content: str
    prompt_id: str
    prompt_version: str
    score: int
    verdict: Literal["pass", "fail"]
    needs_review: bool
    validation_unavailable: bool
    created_at: datetime
    attempts: list[AttemptSummary]


class AdvanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["approve", "edit", "regenerate"]
    content: str | None = None
    note: str | None = None


class ReviseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage_id: str


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detail: str
