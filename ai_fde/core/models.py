"""Core domain models. No vendor SDK, no SQL, no FastAPI imports here."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

DocumentType = Literal["pptx", "pdf", "md", "zip"]


class ParsedSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    heading: str
    text: str


class ParsedDocument(BaseModel):
    """The output of a DocumentParser adapter — crosses the parser/core boundary."""

    model_config = ConfigDict(strict=True, extra="forbid")

    filename: str
    type: DocumentType
    page_or_slide_count: int = Field(ge=0)
    sections: list[ParsedSection] = Field(default_factory=list)
    char_count: int = Field(ge=0)
    content: str


class LLMUsage(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    cost_usd: float = Field(ge=0)


class LLMResponse(BaseModel):
    """What an LLMClient adapter returns — crosses the provider/core boundary."""

    model_config = ConfigDict(strict=True, extra="forbid")

    content: str
    model: str
    usage: LLMUsage


class Attempt(BaseModel):
    """One generation attempt for a stage (original or repair)."""

    model_config = ConfigDict(extra="forbid")

    stage_id: str
    attempt_number: int = Field(ge=1)
    content: str
    prompt_id: str
    prompt_version: str
    generator_model: str
    usage: LLMUsage
    validation_report: dict[str, Any] | None = None
    created_at: datetime


class StageArtifact(BaseModel):
    """The accepted artifact for a stage — the record of what was kept and why."""

    model_config = ConfigDict(extra="forbid")

    stage_id: str
    content: str
    prompt_id: str
    prompt_version: str
    score: int = Field(ge=0, le=100)
    verdict: Literal["pass", "fail"]
    needs_review: bool = False
    validation_unavailable: bool = False
    created_at: datetime
