"""Generator models routinely wrap an entire Markdown artifact in one outer
```markdown ... ``` fence despite being asked for raw Markdown -- this is what
made a real Domain Model artifact render as one giant literal code block
against a live Azure deployment. Pinning the stripping behaviour directly."""

from __future__ import annotations

from ai_fde.core.pipeline.graph import _strip_outer_markdown_fence

BODY = "# Title\n\nSome **content** with a table:\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"


def test_strips_outer_fence_with_markdown_language_tag() -> None:
    assert _strip_outer_markdown_fence(f"```markdown\n{BODY}\n```") == BODY


def test_strips_outer_fence_with_md_language_tag() -> None:
    assert _strip_outer_markdown_fence(f"```md\n{BODY}\n```") == BODY


def test_strips_outer_fence_with_no_language_tag() -> None:
    assert _strip_outer_markdown_fence(f"```\n{BODY}\n```") == BODY


def test_leaves_unfenced_content_untouched() -> None:
    assert _strip_outer_markdown_fence(BODY) == BODY


def test_preserves_inner_fenced_code_blocks_not_at_the_outer_boundary() -> None:
    """A Mermaid/PlantUML diagram fenced inside the real content must survive --
    only a fence wrapping the *entire* response is stripped."""
    body_with_diagram = (
        "# Architecture\n\n```mermaid\ngraph TD;\nA-->B;\n```\n\nMore prose after the diagram.\n"
    )
    wrapped = f"```markdown\n{body_with_diagram}\n```"
    result = _strip_outer_markdown_fence(wrapped)
    assert result == body_with_diagram
    assert "```mermaid" in result


def test_does_not_strip_a_fence_that_is_only_part_of_the_content() -> None:
    only_a_code_example = "Here's a snippet:\n\n```python\nprint('hi')\n```\n\nThat's it."
    assert _strip_outer_markdown_fence(only_a_code_example) == only_a_code_example
