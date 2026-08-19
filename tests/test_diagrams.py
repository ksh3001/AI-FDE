from __future__ import annotations

from ai_fde.core.pipeline.diagrams import render_diagrams_in_markdown

_PNG_BYTES = b"\x89PNG\r\n\x1a\nfake-png-bytes"


class _FakeRenderer:
    def __init__(self, *, fail_on: set[str] | None = None) -> None:
        self.calls: list[str] = []
        self._fail_on = fail_on or set()

    async def render_png(self, source: str) -> bytes:
        self.calls.append(source)
        if source in self._fail_on:
            raise RuntimeError("renderer unreachable")
        return _PNG_BYTES


class _FakeArtifactStore:
    def __init__(self) -> None:
        self.text_files: dict[str, str] = {}
        self.binary_files: dict[str, bytes] = {}

    async def save_artifact(self, run_id: str, stage_id: str, filename: str, content: str) -> None:
        self.text_files[f"{run_id}/{stage_id}/{filename}"] = content

    async def save_binary_artifact(self, run_id: str, stage_id: str, filename: str, content: bytes) -> None:
        self.binary_files[f"{run_id}/{stage_id}/{filename}"] = content

    async def load_artifact(self, run_id: str, stage_id: str, filename: str) -> str:
        return self.text_files[f"{run_id}/{stage_id}/{filename}"]

    async def list_artifacts(self, run_id: str) -> list[str]:
        return []


async def test_render_diagrams_in_markdown_returns_content_unchanged_without_diagrams() -> None:
    content = "# Just prose\n\nNo diagrams here.\n"
    store = _FakeArtifactStore()
    renderer = _FakeRenderer()

    result = await render_diagrams_in_markdown(
        content, renderer=renderer, artifact_store=store, run_id="run1", stage_id="architecture"
    )

    assert result == content
    assert renderer.calls == []


async def test_render_diagrams_in_markdown_embeds_png_and_saves_files() -> None:
    content = (
        "# Architecture\n\n"
        "```plantuml\n@startuml\nrectangle A\n@enduml\n```\n\n"
        "Some prose in between.\n\n"
        "```plantuml\n@startuml\nrectangle B\n@enduml\n```\n"
    )
    store = _FakeArtifactStore()
    renderer = _FakeRenderer()

    result = await render_diagrams_in_markdown(
        content, renderer=renderer, artifact_store=store, run_id="run1", stage_id="architecture"
    )

    assert "```plantuml" not in result
    assert "![Diagram 1](data:image/png;base64," in result
    assert "![Diagram 2](data:image/png;base64," in result
    assert "Some prose in between." in result
    assert len(renderer.calls) == 2

    assert store.text_files["run1/architecture/diagrams/diagram-1.puml"] == "@startuml\nrectangle A\n@enduml"
    assert store.text_files["run1/architecture/diagrams/diagram-2.puml"] == "@startuml\nrectangle B\n@enduml"
    assert store.binary_files["run1/architecture/diagrams/diagram-1.png"] == _PNG_BYTES
    assert store.binary_files["run1/architecture/diagrams/diagram-2.png"] == _PNG_BYTES


async def test_render_diagrams_in_markdown_degrades_a_failed_diagram_without_raising() -> None:
    source = "@startuml\nrectangle A\n@enduml"
    content = f"# Architecture\n\n```plantuml\n{source}\n```\n"
    store = _FakeArtifactStore()
    renderer = _FakeRenderer(fail_on={source})

    result = await render_diagrams_in_markdown(
        content, renderer=renderer, artifact_store=store, run_id="run1", stage_id="architecture"
    )

    assert "diagram rendering unavailable" in result
    assert "```plantuml" in result  # original source preserved for the reader
    assert source in result
    assert store.binary_files == {}
    assert store.text_files == {}
