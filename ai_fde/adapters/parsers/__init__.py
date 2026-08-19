"""pptx / pdf / md / zip DocumentParser adapters, selected by filename extension."""

from __future__ import annotations

from ai_fde.core.ports import DocumentParser
from ai_fde.adapters.parsers.md_parser import MarkdownParser
from ai_fde.adapters.parsers.pdf_parser import PdfParser
from ai_fde.adapters.parsers.pptx_parser import PptxParser
from ai_fde.adapters.parsers.repo_zip_parser import RepoZipParser

ALL_PARSERS: tuple[DocumentParser, ...] = (PptxParser(), PdfParser(), MarkdownParser(), RepoZipParser())


def select_parser(filename: str) -> DocumentParser:
    for parser in ALL_PARSERS:
        if parser.supports(filename):
            return parser
    raise ValueError(f"unsupported file type: {filename!r} (expected .pptx, .pdf, .md, or .zip)")
