from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from ai_fde.adapters.parsers import select_parser
from ai_fde.adapters.parsers.md_parser import MarkdownParser
from ai_fde.adapters.parsers.pdf_parser import PdfParser
from ai_fde.adapters.parsers.pptx_parser import PptxParser
from ai_fde.adapters.parsers import repo_zip_parser
from ai_fde.adapters.parsers.repo_zip_parser import RepoZipParser

FIXTURES = Path(__file__).parent / "fixtures"


def _read(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def _make_zip(files: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for name, text in files.items():
            zf.writestr(name, text)
    return buffer.getvalue()


async def test_pptx_parser_extracts_slides_notes_and_tables() -> None:
    doc = await PptxParser().parse(_read("three_slide.pptx"), "three_slide.pptx")

    assert doc.type == "pptx"
    assert doc.page_or_slide_count == 3
    assert len(doc.sections) == 3
    assert doc.sections[0].heading == "Overview"
    assert "maintenance backlog triage" in doc.content
    assert "Speaker note for slide 1" in doc.content
    assert "CMMS" in doc.content  # from the table on slide 2
    assert doc.char_count == len(doc.content)


async def test_pdf_parser_extracts_per_page_text() -> None:
    doc = await PdfParser().parse(_read("two_page.pdf"), "two_page.pdf")

    assert doc.type == "pdf"
    assert doc.page_or_slide_count == 2
    assert doc.sections[0].heading == "Page 1"
    assert doc.sections[1].heading == "Page 2"
    assert "Evidence intake summary" in doc.content
    assert "advisory only" in doc.content


async def test_pdf_parser_fails_clearly_on_no_extractable_text() -> None:
    with pytest.raises(ValueError, match="no extractable text"):
        await PdfParser().parse(_read("blank_no_text.pdf"), "blank_no_text.pdf")


async def test_md_parser_is_verbatim_and_splits_sections() -> None:
    raw = _read("use_case.md")
    doc = await MarkdownParser().parse(raw, "use_case.md")

    assert doc.type == "md"
    assert doc.content == raw.decode("utf-8")
    headings = [s.heading for s in doc.sections]
    assert headings == ["Maintenance Backlog Triage", "Situation", "Problem", "Constraints"]


async def test_repo_zip_parser_extracts_files_and_builds_tree() -> None:
    archive = _make_zip(
        {
            "README.md": "# Widget Service\n\nHandles widget orchestration.",
            "src/main.py": "def main():\n    pass\n",
            "src/utils.py": "def helper():\n    return 1\n",
            "assets/logo.png": "\x89PNG\r\n\x1a\nnot-really-a-png-but-binary-ish",
        }
    )
    doc = await RepoZipParser().parse(archive, "widget-service.zip")

    assert doc.type == "zip"
    assert doc.page_or_slide_count == 4  # every non-dir entry, including the skipped binary
    assert "src/main.py" in doc.content  # listed in the file tree
    assert "Widget Service" in doc.content
    assert "def main" in doc.content
    headings = {s.heading for s in doc.sections}
    assert "README.md" in headings
    assert "src/main.py" in headings
    assert "assets/logo.png" not in headings  # not a recognized text extension
    assert doc.char_count == len(doc.content)


async def test_repo_zip_parser_skips_noise_directories() -> None:
    archive = _make_zip(
        {
            "src/app.py": "print('hi')\n",
            "node_modules/pkg/index.js": "module.exports = {};\n",
            ".venv/lib/site.py": "# vendored\n",
            ".git/HEAD": "ref: refs/heads/main\n",
        }
    )
    doc = await RepoZipParser().parse(archive, "repo.zip")

    assert doc.page_or_slide_count == 1  # only src/app.py survives the noise filter
    assert "node_modules" not in doc.content
    assert ".venv" not in doc.content
    assert ".git" not in doc.content


async def test_repo_zip_parser_prioritizes_readme_and_manifests_over_budget() -> None:
    archive = _make_zip(
        {
            "src/z_last.py": "z = 1\n",
            "pyproject.toml": "[project]\nname = 'demo'\n",
            "README.md": "# Demo\n",
        }
    )
    doc = await RepoZipParser().parse(archive, "repo.zip")

    order = [s.heading for s in doc.sections]
    assert order.index("README.md") < order.index("pyproject.toml") < order.index("src/z_last.py")


async def test_repo_zip_parser_respects_content_char_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(repo_zip_parser, "_TOTAL_CONTENT_CHAR_BUDGET", 10)
    archive = _make_zip({"a.py": "a" * 20, "b.py": "b" * 20})

    doc = await RepoZipParser().parse(archive, "repo.zip")

    assert len(doc.sections) == 1  # budget exhausted after the first file
    assert "additional text file(s) not shown" in doc.content


async def test_repo_zip_parser_rejects_bad_zip() -> None:
    with pytest.raises(ValueError, match="could not be opened as a zip"):
        await RepoZipParser().parse(b"not a zip", "broken.zip")


async def test_repo_zip_parser_rejects_empty_zip() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w"):
        pass
    with pytest.raises(ValueError, match="zip archive is empty"):
        await RepoZipParser().parse(buffer.getvalue(), "empty.zip")


async def test_repo_zip_parser_rejects_when_no_text_files() -> None:
    archive = _make_zip({"image.bin": "\x00\x01\x02binary"})
    with pytest.raises(ValueError, match="no readable source/text files"):
        await RepoZipParser().parse(archive, "binary-only.zip")


def test_select_parser_dispatches_by_extension() -> None:
    assert isinstance(select_parser("deck.pptx"), PptxParser)
    assert isinstance(select_parser("report.PDF"), PdfParser)
    assert isinstance(select_parser("notes.md"), MarkdownParser)
    assert isinstance(select_parser("repo.ZIP"), RepoZipParser)


def test_select_parser_rejects_unsupported_extension() -> None:
    with pytest.raises(ValueError, match="unsupported file type"):
        select_parser("archive.rar")
