"""Persistent run metadata, accepted stage artifacts, and the SSE event log.

Separate from LangGraph's own SQLite checkpoint file (which owns per-stage graph
execution state) -- this store owns what the API/UI needs: run lifecycle,
accepted artifacts, and replayable events. "Long runs must survive a page
refresh" per the build spec means this data lives here, not in memory.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite

from ai_fde.core.models import Attempt, ParsedDocument, StageArtifact
from ai_fde.core.pipeline.state import IllegalTransitionError, RunMode, RunStatus, validate_transition

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    mode TEXT NOT NULL,
    current_stage TEXT,
    failed_stage TEXT,
    failure_reason TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    use_case_json TEXT,
    evidence_json TEXT,
    domain_config_json TEXT
);

CREATE TABLE IF NOT EXISTS stage_artifacts (
    run_id TEXT NOT NULL,
    stage_id TEXT NOT NULL,
    content TEXT NOT NULL,
    prompt_id TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    score INTEGER NOT NULL,
    verdict TEXT NOT NULL,
    needs_review INTEGER NOT NULL,
    validation_unavailable INTEGER NOT NULL,
    validation_report_json TEXT,
    attempts_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (run_id, stage_id)
);

CREATE TABLE IF NOT EXISTS events (
    run_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    type TEXT NOT NULL,
    stage_id TEXT,
    data_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (run_id, seq)
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RunRecord:
    run_id: str
    status: RunStatus
    mode: RunMode
    current_stage: str | None
    failed_stage: str | None
    failure_reason: str | None
    created_at: str
    use_case: ParsedDocument | None
    evidence: list[ParsedDocument]
    domain_config: dict[str, str]


class RunNotFoundError(LookupError):
    pass


class RunStore:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    @classmethod
    async def create(cls, db_path: Path) -> RunStore:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = await aiosqlite.connect(str(db_path))
        conn.row_factory = aiosqlite.Row
        await conn.executescript(_SCHEMA)
        await conn.commit()
        return cls(conn)

    async def close(self) -> None:
        await self._conn.close()

    async def create_run(
        self,
        *,
        run_id: str,
        mode: RunMode,
        use_case: ParsedDocument | None,
        evidence: list[ParsedDocument],
        domain_config: dict[str, str],
    ) -> None:
        now = _now()
        await self._conn.execute(
            """INSERT INTO runs
               (run_id, status, mode, current_stage, failed_stage, failure_reason,
                created_at, updated_at, use_case_json, evidence_json, domain_config_json)
               VALUES (?, 'queued', ?, NULL, NULL, NULL, ?, ?, ?, ?, ?)""",
            (
                run_id,
                mode,
                now,
                now,
                use_case.model_dump_json() if use_case else None,
                json.dumps([d.model_dump() for d in evidence]),
                json.dumps(domain_config),
            ),
        )
        await self._conn.commit()

    async def get_run(self, run_id: str) -> RunRecord:
        cursor = await self._conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,))
        row = await cursor.fetchone()
        if row is None:
            raise RunNotFoundError(run_id)
        return self._row_to_record(row)

    async def list_runs_by_status(self, *statuses: RunStatus) -> list[RunRecord]:
        placeholders = ",".join("?" for _ in statuses)
        cursor = await self._conn.execute(
            f"SELECT * FROM runs WHERE status IN ({placeholders})", statuses
        )
        rows = await cursor.fetchall()
        return [self._row_to_record(row) for row in rows]

    def _row_to_record(self, row: aiosqlite.Row) -> RunRecord:
        use_case = ParsedDocument.model_validate_json(row["use_case_json"]) if row["use_case_json"] else None
        evidence = [ParsedDocument.model_validate(d) for d in json.loads(row["evidence_json"] or "[]")]
        return RunRecord(
            run_id=row["run_id"],
            status=row["status"],
            mode=row["mode"],
            current_stage=row["current_stage"],
            failed_stage=row["failed_stage"],
            failure_reason=row["failure_reason"],
            created_at=row["created_at"],
            use_case=use_case,
            evidence=evidence,
            domain_config=json.loads(row["domain_config_json"] or "{}"),
        )

    async def set_parsed_documents(
        self, run_id: str, *, use_case: ParsedDocument, evidence: list[ParsedDocument]
    ) -> None:
        await self._conn.execute(
            "UPDATE runs SET use_case_json = ?, evidence_json = ?, updated_at = ? WHERE run_id = ?",
            (use_case.model_dump_json(), json.dumps([d.model_dump() for d in evidence]), _now(), run_id),
        )
        await self._conn.commit()

    async def transition(
        self,
        run_id: str,
        target: RunStatus,
        *,
        current_stage: str | None = None,
        failed_stage: str | None = None,
        failure_reason: str | None = None,
    ) -> RunRecord:
        record = await self.get_run(run_id)
        validate_transition(record.status, target)  # raises IllegalTransitionError

        await self._conn.execute(
            """UPDATE runs SET status = ?, current_stage = COALESCE(?, current_stage),
               failed_stage = ?, failure_reason = ?, updated_at = ? WHERE run_id = ?""",
            (target, current_stage, failed_stage, failure_reason, _now(), run_id),
        )
        await self._conn.commit()
        return await self.get_run(run_id)

    async def force_status(self, run_id: str, status: RunStatus, *, failure_reason: str | None = None) -> None:
        """Bypasses transition validation -- only for startup crash recovery."""
        await self._conn.execute(
            "UPDATE runs SET status = ?, failure_reason = ?, updated_at = ? WHERE run_id = ?",
            (status, failure_reason, _now(), run_id),
        )
        await self._conn.commit()

    async def save_stage_artifact(
        self, run_id: str, artifact: StageArtifact, attempts: list[Attempt]
    ) -> None:
        await self._conn.execute(
            """INSERT INTO stage_artifacts
               (run_id, stage_id, content, prompt_id, prompt_version, score, verdict,
                needs_review, validation_unavailable, validation_report_json, attempts_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(run_id, stage_id) DO UPDATE SET
                 content=excluded.content, prompt_id=excluded.prompt_id,
                 prompt_version=excluded.prompt_version, score=excluded.score,
                 verdict=excluded.verdict, needs_review=excluded.needs_review,
                 validation_unavailable=excluded.validation_unavailable,
                 validation_report_json=excluded.validation_report_json,
                 attempts_json=excluded.attempts_json, created_at=excluded.created_at""",
            (
                run_id,
                artifact.stage_id,
                artifact.content,
                artifact.prompt_id,
                artifact.prompt_version,
                artifact.score,
                artifact.verdict,
                int(artifact.needs_review),
                int(artifact.validation_unavailable),
                None,
                json.dumps([a.model_dump(mode="json") for a in attempts]),
                artifact.created_at.isoformat(),
            ),
        )
        await self._conn.commit()

    async def get_stage_artifact(self, run_id: str, stage_id: str) -> StageArtifact | None:
        cursor = await self._conn.execute(
            "SELECT * FROM stage_artifacts WHERE run_id = ? AND stage_id = ?", (run_id, stage_id)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_artifact(row)

    async def get_stage_attempts(self, run_id: str, stage_id: str) -> list[dict[str, Any]] | None:
        cursor = await self._conn.execute(
            "SELECT attempts_json FROM stage_artifacts WHERE run_id = ? AND stage_id = ?",
            (run_id, stage_id),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return json.loads(row["attempts_json"])

    async def delete_stage_artifacts(self, run_id: str, stage_ids: list[str]) -> None:
        """Used by revise_stage: a stage being revised, and everything after it, was
        accepted on top of context that's about to change, so all of it must be
        regenerated -- not just the one stage a human pointed at."""
        if not stage_ids:
            return
        placeholders = ",".join("?" for _ in stage_ids)
        await self._conn.execute(
            f"DELETE FROM stage_artifacts WHERE run_id = ? AND stage_id IN ({placeholders})",
            (run_id, *stage_ids),
        )
        await self._conn.commit()

    async def list_stage_artifacts(self, run_id: str) -> list[StageArtifact]:
        cursor = await self._conn.execute(
            "SELECT * FROM stage_artifacts WHERE run_id = ? ORDER BY created_at", (run_id,)
        )
        rows = await cursor.fetchall()
        return [self._row_to_artifact(row) for row in rows]

    @staticmethod
    def _row_to_artifact(row: aiosqlite.Row) -> StageArtifact:
        return StageArtifact(
            stage_id=row["stage_id"],
            content=row["content"],
            prompt_id=row["prompt_id"],
            prompt_version=row["prompt_version"],
            score=row["score"],
            verdict=row["verdict"],
            needs_review=bool(row["needs_review"]),
            validation_unavailable=bool(row["validation_unavailable"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    async def append_event(
        self, run_id: str, *, type: str, stage_id: str | None, data: dict[str, Any]
    ) -> int:
        cursor = await self._conn.execute(
            "SELECT COALESCE(MAX(seq), 0) + 1 FROM events WHERE run_id = ?", (run_id,)
        )
        (seq,) = await cursor.fetchone()
        await self._conn.execute(
            "INSERT INTO events (run_id, seq, type, stage_id, data_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (run_id, seq, type, stage_id, json.dumps(data), _now()),
        )
        await self._conn.commit()
        return seq

    async def get_latest_event(self, run_id: str, *, stage_id: str, type: str) -> dict[str, Any] | None:
        cursor = await self._conn.execute(
            """SELECT seq, type, stage_id, data_json FROM events
               WHERE run_id = ? AND stage_id = ? AND type = ? ORDER BY seq DESC LIMIT 1""",
            (run_id, stage_id, type),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return {"seq": row["seq"], "type": row["type"], "stage_id": row["stage_id"], "data": json.loads(row["data_json"])}

    async def list_events_after(self, run_id: str, after_seq: int) -> list[dict[str, Any]]:
        cursor = await self._conn.execute(
            "SELECT seq, type, stage_id, data_json FROM events WHERE run_id = ? AND seq > ? ORDER BY seq",
            (run_id, after_seq),
        )
        rows = await cursor.fetchall()
        return [
            {"seq": r["seq"], "type": r["type"], "stage_id": r["stage_id"], "data": json.loads(r["data_json"])}
            for r in rows
        ]
