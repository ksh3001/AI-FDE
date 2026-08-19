"""Markdown parser — content is passed through verbatim, sections split on headings."""

from __future__ import annotations

import re

from ai_fde.core.models import ParsedDocument, ParsedSection

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)


class MarkdownParser:
    def supports(self, filename: str) -> bool:
        return filename.lower().endswith(".md")

    async def parse(self, content: bytes, filename: str) -> ParsedDocument:
        text = content.decode("utf-8")
        sections = _split_sections(text)
        return ParsedDocument(
            filename=filename,
            type="md",
            page_or_slide_count=1,
            sections=sections,
            char_count=len(text),
            content=text,
        )


def _split_sections(text: str) -> list[ParsedSection]:
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        return [ParsedSection(heading="(untitled)", text=text.strip())] if text.strip() else []

    sections: list[ParsedSection] = []
    for i, match in enumerate(matches):
        heading = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append(ParsedSection(heading=heading, text=text[start:end].strip()))
    return sections
