"""Repo zip parser — the use case can be a zipped source repository instead of
a written spec; this turns it into a file tree plus a budget-capped set of
file contents so downstream stages can derive discovery/architecture/ADRs
straight from code.

A real repo can trivially blow past what fits in an LLM prompt, and zip
archives can lie about their size, so this never returns file bytes verbatim.
It walks the archive under a hard entry-count/byte ceiling, drops known noise
directories (.git, node_modules, .venv, build output, ...) and non-text
files, then fills a fixed character budget in priority order -- README first,
then manifests (package.json, pyproject.toml, ...), then source, shallowest
paths first -- so the model always sees the shape of the repo even when most
file bodies end up truncated or omitted.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import PurePosixPath

from ai_fde.core.models import ParsedDocument, ParsedSection

_NOISE_DIR_NAMES = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", ".nuxt", "target", "vendor", ".idea", ".vscode",
    "coverage", ".pytest_cache", ".mypy_cache", ".tox", ".gradle", ".cache",
    ".parcel-cache", "site-packages", "bower_components",
}

_TEXT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".java", ".kt",
    ".kts", ".rb", ".php", ".cs", ".cpp", ".cc", ".c", ".h", ".hpp", ".rs",
    ".swift", ".scala", ".sql", ".sh", ".bash", ".ps1", ".yaml", ".yml",
    ".json", ".md", ".mdx", ".toml", ".ini", ".cfg", ".graphql", ".proto",
    ".html", ".css", ".scss", ".less", ".vue", ".svelte", ".txt", ".gradle",
}

_PRIORITY_BASENAMES = {
    "readme", "readme.md", "readme.rst", "readme.txt",
    "package.json", "pyproject.toml", "requirements.txt", "setup.py", "setup.cfg",
    "pipfile", "go.mod", "cargo.toml", "pom.xml", "build.gradle", "build.gradle.kts",
    "composer.json", "gemfile", "dockerfile", "docker-compose.yml", "docker-compose.yaml",
    ".env.example", "tsconfig.json",
}

_MAX_ENTRIES = 20_000
_MAX_DECLARED_UNCOMPRESSED_BYTES = 200_000_000  # reject before reading anything -- zip bomb guard
_TOTAL_CONTENT_CHAR_BUDGET = 150_000
_PER_FILE_CHAR_CAP = 8_000
_MAX_TREE_ENTRIES = 5_000


def _is_noise_path(path: PurePosixPath) -> bool:
    return any(part in _NOISE_DIR_NAMES for part in path.parts[:-1])


def _is_text_file(path: PurePosixPath) -> bool:
    name = path.name.lower()
    return name in _PRIORITY_BASENAMES or path.suffix.lower() in _TEXT_EXTENSIONS


def _priority_rank(path: PurePosixPath) -> tuple[int, int, str]:
    name = path.name.lower()
    if name.startswith("readme"):
        rank = 0
    elif name in _PRIORITY_BASENAMES:
        rank = 1
    else:
        rank = 2
    return (rank, len(path.parts), str(path))


class RepoZipParser:
    def supports(self, filename: str) -> bool:
        return filename.lower().endswith(".zip")

    async def parse(self, content: bytes, filename: str) -> ParsedDocument:
        try:
            archive = zipfile.ZipFile(io.BytesIO(content))
        except zipfile.BadZipFile as exc:
            raise ValueError(f"{filename}: could not be opened as a zip archive: {exc}") from exc

        infos = [i for i in archive.infolist() if not i.is_dir()]
        if len(infos) > _MAX_ENTRIES:
            raise ValueError(f"{filename}: archive has too many entries (> {_MAX_ENTRIES})")

        declared_total = sum(i.file_size for i in infos)
        if declared_total > _MAX_DECLARED_UNCOMPRESSED_BYTES:
            limit_mb = _MAX_DECLARED_UNCOMPRESSED_BYTES // 1_000_000
            raise ValueError(f"{filename}: archive is too large uncompressed (> {limit_mb}MB)")

        all_paths: list[PurePosixPath] = []
        candidates: list[tuple[PurePosixPath, zipfile.ZipInfo]] = []
        for info in infos:
            path = PurePosixPath(info.filename)
            if _is_noise_path(path):
                continue
            all_paths.append(path)
            if _is_text_file(path):
                candidates.append((path, info))

        if not all_paths:
            raise ValueError(f"{filename}: zip archive is empty")

        candidates.sort(key=lambda pair: _priority_rank(pair[0]))

        sections: list[ParsedSection] = []
        budget_remaining = _TOTAL_CONTENT_CHAR_BUDGET
        for path, info in candidates:
            if budget_remaining <= 0:
                break
            try:
                text = archive.read(info).decode("utf-8")
            except (UnicodeDecodeError, zipfile.BadZipFile):
                continue  # binary despite the extension guess, or unreadable -- skip silently

            cap = min(_PER_FILE_CHAR_CAP, budget_remaining)
            body = text[:cap]
            if len(body) < len(text):
                body += "\n... (truncated)"
            sections.append(ParsedSection(heading=str(path), text=body))
            budget_remaining -= len(body)

        if not sections:
            raise ValueError(f"{filename}: no readable source/text files found in this archive")

        omitted = len(candidates) - len(sections)

        tree_paths = sorted(str(p) for p in all_paths)
        tree_note = ""
        if len(tree_paths) > _MAX_TREE_ENTRIES:
            tree_note = f"\n... ({len(tree_paths) - _MAX_TREE_ENTRIES} more files not shown)"
            tree_paths = tree_paths[:_MAX_TREE_ENTRIES]

        content_blocks = "\n\n".join(f"### {s.heading}\n\n```\n{s.text}\n```" for s in sections)
        omitted_note = (
            f"\n\n({omitted} additional text file(s) not shown -- content budget reached)"
            if omitted > 0
            else ""
        )

        full_text = (
            f"## Repository: {filename}\n\n"
            f"## File tree ({len(all_paths)} files)\n\n" + "\n".join(tree_paths) + tree_note + "\n\n"
            f"## File contents\n\n{content_blocks}{omitted_note}"
        )

        return ParsedDocument(
            filename=filename,
            type="zip",
            page_or_slide_count=len(all_paths),
            sections=sections,
            char_count=len(full_text),
            content=full_text,
        )
