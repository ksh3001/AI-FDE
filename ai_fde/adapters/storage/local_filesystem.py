"""Local filesystem ArtifactStore -- runs/{run_id}/{stage_id}/{filename}."""

from __future__ import annotations

import asyncio
from pathlib import Path


class LocalFilesystemArtifactStore:
    def __init__(self, root: Path) -> None:
        self._root = root

    def _path(self, run_id: str, stage_id: str, filename: str) -> Path:
        return self._root / run_id / stage_id / filename

    async def save_artifact(self, run_id: str, stage_id: str, filename: str, content: str) -> None:
        path = self._path(run_id, stage_id, filename)
        await asyncio.to_thread(self._write, path, content)

    async def save_binary_artifact(self, run_id: str, stage_id: str, filename: str, content: bytes) -> None:
        path = self._path(run_id, stage_id, filename)
        await asyncio.to_thread(self._write_bytes, path, content)

    async def load_artifact(self, run_id: str, stage_id: str, filename: str) -> str:
        path = self._path(run_id, stage_id, filename)
        return await asyncio.to_thread(path.read_text, "utf-8")

    async def list_artifacts(self, run_id: str) -> list[str]:
        run_dir = self._root / run_id
        if not run_dir.is_dir():
            return []

        def _list() -> list[str]:
            return sorted(
                str(p.relative_to(run_dir)) for p in run_dir.rglob("*") if p.is_file()
            )

        return await asyncio.to_thread(_list)

    @staticmethod
    def _write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    @staticmethod
    def _write_bytes(path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
