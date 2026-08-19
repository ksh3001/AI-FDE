"""Renders every fenced ```plantuml block in a stage's final markdown to PNG
and rewrites the block into an embedded image, so the artifact always
displays correctly wherever the markdown is viewed -- in the app, in the
downloaded bundle's .md, in any plain markdown viewer -- with no dependency
on client-side diagram-library JS at read time.

Generic by design: it runs on any stage's final draft, not just the
architecture stage, so a future stage that emits a plantuml block picks this
up for free with zero pipeline.yaml/Python changes.

Never raises past a single diagram's boundary -- a render failure (the
renderer unreachable, a malformed diagram) degrades that one block in place
rather than failing the whole stage, mirroring the existing
validation_unavailable degrade-not-crash pattern for a malformed validator
response.
"""

from __future__ import annotations

import base64
import re

from ai_fde.core.ports import ArtifactStore, DiagramRenderer

_PLANTUML_FENCE_RE = re.compile(r"```plantuml\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


async def render_diagrams_in_markdown(
    content: str,
    *,
    renderer: DiagramRenderer,
    artifact_store: ArtifactStore,
    run_id: str,
    stage_id: str,
) -> str:
    matches = list(_PLANTUML_FENCE_RE.finditer(content))
    if not matches:
        return content

    replacements: list[tuple[str, str]] = []
    for i, match in enumerate(matches, start=1):
        source = match.group(1).strip()
        try:
            png = await renderer.render_png(source)
        except Exception as exc:  # noqa: BLE001 - a diagram render failure must never fail the stage
            replacement = (
                f"> ⚠️ diagram rendering unavailable: {exc}\n\n"
                f"```plantuml\n{source}\n```"
            )
            replacements.append((match.group(0), replacement))
            continue

        await artifact_store.save_artifact(run_id, stage_id, f"diagrams/diagram-{i}.puml", source)
        await artifact_store.save_binary_artifact(run_id, stage_id, f"diagrams/diagram-{i}.png", png)

        b64 = base64.b64encode(png).decode("ascii")
        replacements.append((match.group(0), f"![Diagram {i}](data:image/png;base64,{b64})"))

    result = content
    for original, replacement in replacements:
        result = result.replace(original, replacement, 1)
    return result
