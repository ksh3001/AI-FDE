from __future__ import annotations

import itertools

import pytest

from ai_fde.core.pipeline.state import (
    TERMINAL_STATUSES,
    IllegalTransitionError,
    RunStatus,
    validate_transition,
)

ALL_STATUSES: tuple[RunStatus, ...] = (
    "queued",
    "parsing",
    "running",
    "awaiting_approval",
    "complete",
    "failed",
    "cancelled",
)

LEGAL_TRANSITIONS: set[tuple[RunStatus, RunStatus]] = {
    ("queued", "parsing"),
    ("parsing", "running"),
    ("parsing", "failed"),
    ("running", "awaiting_approval"),
    ("running", "complete"),
    ("running", "failed"),
    ("running", "cancelled"),
    ("awaiting_approval", "running"),
    ("awaiting_approval", "cancelled"),
    ("failed", "running"),
    # A human may explicitly send an earlier stage back for revision even after the
    # run completed -- see PipelineRunner.revise_stage. "complete" stays in
    # TERMINAL_STATUSES (nothing proceeds from it on its own); this is the one
    # deliberate, explicit exception, not a hole in "terminal."
    ("complete", "running"),
}


@pytest.mark.parametrize("current,target", sorted(LEGAL_TRANSITIONS))
def test_every_declared_transition_is_accepted(current: RunStatus, target: RunStatus) -> None:
    validate_transition(current, target)  # must not raise


@pytest.mark.parametrize(
    "current,target",
    sorted(
        (current, target)
        for current, target in itertools.product(ALL_STATUSES, ALL_STATUSES)
        if (current, target) not in LEGAL_TRANSITIONS
    ),
)
def test_every_undeclared_transition_is_rejected(current: RunStatus, target: RunStatus) -> None:
    with pytest.raises(IllegalTransitionError):
        validate_transition(current, target)


@pytest.mark.parametrize("terminal", sorted(TERMINAL_STATUSES))
def test_terminal_statuses_reject_everything_except_declared_exceptions(terminal: RunStatus) -> None:
    """"Terminal" means nothing proceeds automatically from here -- not literally zero
    outgoing transitions ever. "complete" has exactly one declared exception
    (-> running, for an explicit revise); "cancelled" still has none."""
    for target in ALL_STATUSES:
        if (terminal, target) in LEGAL_TRANSITIONS:
            continue
        with pytest.raises(IllegalTransitionError):
            validate_transition(terminal, target)


def test_cancelled_is_fully_terminal_with_no_exceptions() -> None:
    for target in ALL_STATUSES:
        with pytest.raises(IllegalTransitionError):
            validate_transition("cancelled", target)


def test_illegal_transition_error_names_current_and_target() -> None:
    with pytest.raises(IllegalTransitionError) as exc_info:
        validate_transition("cancelled", "running")
    assert exc_info.value.current == "cancelled"
    assert exc_info.value.target == "running"


def test_self_transitions_are_rejected_unless_declared() -> None:
    for status in ALL_STATUSES:
        with pytest.raises(IllegalTransitionError):
            validate_transition(status, status)
