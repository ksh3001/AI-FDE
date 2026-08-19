"""PDF parser — per-page text, page numbers preserved.

Fails with a clear error rather than emitting empty output when a PDF has no
extractable text (e.g. a scanned document with no OCR layer).
"""

from __future__ import annotations

import io

import pdfplumber

from ai_fde.core.models import ParsedDocument, ParsedSection


class PdfParser:
    def supports(self, filename: str) -> bool:
        return filename.lower().endswith(".pdf")

    async def parse(self, content: bytes, filename: str) -> ParsedDocument:
        sections: list[ParsedSection] = []
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for index, page in enumerate(pdf.pages, start=1):
                    text = (page.extract_text() or "").strip()
                    sections.append(ParsedSection(heading=f"Page {index}", text=text))
        except Exception as exc:  # noqa: BLE001 - pdfplumber raises various parser errors
            raise ValueError(f"{filename}: could not be opened as a PDF: {exc}") from exc

        if not sections:
            raise ValueError(f"{filename}: PDF has no pages")

        if not any(s.text for s in sections):
            raise ValueError(
                f"{filename}: no extractable text — scanned document? "
                "AI_FDE does not OCR image-only PDFs."
            )

        full_text = "\n\n".join(f"## {s.heading}\n\n{s.text}" for s in sections if s.text)

        return ParsedDocument(
            filename=filename,
            type="pdf",
            page_or_slide_count=len(sections),
            sections=sections,
            char_count=len(full_text),
            content=full_text,
        )
