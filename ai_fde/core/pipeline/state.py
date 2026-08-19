"""Run status state machine and the LangGraph-shaped RunState.

Declares exactly the transitions the build spec lists and rejects everything else.
"""

from __future__ import annotations

from typing import Literal, TypedDict

from ai_fde.core.models import Attempt, ParsedDocument, StageArtifact
from ai_fde.core.validation.models import ValidationReport

RunStatus = Literal[
    "queued", "parsing", "running", "awaiting_approval", "complete", "failed", "cancelled"
]
RunMode = Literal["auto", "stepwise"]

_ALLOWED_TRANSITIONS: dict[RunStatus, frozenset[RunStatus]] = {
    "queued": frozenset({"parsing"}),
    "parsing": frozenset({"running", "failed"}),
    "running": frozenset({"awaiting_approval", "complete", "failed", "cancelled"}),
    "awaiting_approval": frozenset({"running", "cancelled"}),
    "failed": frozenset({"running"}),  # via POST /runs/{id}/resume
    # "complete" is terminal for automatic forward progression (nothing continues on its
    # own from here), but a human may still explicitly send an earlier stage back for
    # revision via POST /runs/{id}/revise -- see PipelineRunner.revise_stage.
    "complete": frozenset({"running"}),
    "cancelled": frozenset(),  # terminal
}

TERMINAL_STATUSES: frozenset[RunStatus] = frozenset({"complete", "cancelled"})


class IllegalTransitionError(ValueError):
    def __init__(self, current: RunStatus, target: RunStatus) -> None:
        self.current = current
        self.target = target
        super().__init__(f"illegal transition: {current!r} -> {target!r}")


def validate_transition(current: RunStatus, target: RunStatus) -> None:
    """Raise IllegalTransitionError unless current -> target is explicitly allowed."""
    if target not in _ALLOWED_TRANSITIONS.get(current, frozenset()):
        raise IllegalTransitionError(current, target)


class RunState(TypedDict):
    run_id: str
    use_case: ParsedDocument
    evidence: list[ParsedDocument]
    artifacts: dict[str, StageArtifact]
    current_stage: str
    validations: dict[str, ValidationReport]
    attempts: dict[str, list[Attempt]]
    mode: RunMode
    status: RunStatus
    failed_stage: str | None
