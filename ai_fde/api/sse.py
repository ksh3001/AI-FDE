"""SSE event shape and replay-from-seq logic — wired into routes/runs.py in Milestone 4.

Declared now so the contract (monotonic `seq`, `Last-Event-ID` replay) is fixed
before the graph exists, per the build spec's resume/reconnect requirements.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

SSEEventType = Literal[
    "stage_started",
    "stage_generated",
    "stage_validated",
    "stage_repaired",
    "stage_awaiting",
    "stage_complete",
    "stage_failed",
]


class SSEEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seq: int
    type: SSEEventType
    stage_id: str
    data: dict[str, str] = {}
