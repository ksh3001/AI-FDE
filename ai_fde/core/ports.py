"""Protocols the core depends on; adapters implement them. No vendor imports here."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ai_fde.core.models import LLMResponse, ParsedDocument


@runtime_checkable
class DocumentParser(Protocol):
    """One parser per input type (.pptx / .pdf / .md / .zip), selected by the adapter layer."""

    def supports(self, filename: str) -> bool: ...

    async def parse(self, content: bytes, filename: str) -> ParsedDocument: ...


@runtime_checkable
class LLMClient(Protocol):
    """The single typed seam every model call flows through."""

    async def complete(self, *, model: str, system: str, prompt: str) -> LLMResponse: ...


@runtime_checkable
class ArtifactStore(Protocol):
    """Persists stage artifacts, attempts, and inputs, keyed by run_id."""

    async def save_artifact(
        self, run_id: str, stage_id: str, filename: str, content: str
    ) -> None: ...

    async def save_binary_artifact(
        self, run_id: str, stage_id: str, filename: str, content: bytes
    ) -> None: ...

    async def load_artifact(self, run_id: str, stage_id: str, filename: str) -> str: ...

    async def list_artifacts(self, run_id: str) -> list[str]: ...


@runtime_checkable
class DiagramRenderer(Protocol):
    """Renders a diagram source string (e.g. PlantUML) to PNG bytes."""

    async def render_png(self, source: str) -> bytes: ...
