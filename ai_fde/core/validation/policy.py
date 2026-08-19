"""Threshold and repair policy -- the rules the routing logic in the graph enforces.

Kept as pure functions so the routing logic (Milestone 4) and its tests don't
need a live graph to exercise "accept vs repair vs needs_review".
"""

from __future__ import annotations

from ai_fde.core.validation.models import ValidationReport


def accepts(report: ValidationReport, *, threshold: int) -> bool:
    return report.overall_score >= threshold


def choose_best(
    first: tuple[str, ValidationReport], second: tuple[str, ValidationReport]
) -> tuple[str, ValidationReport]:
    """After the single repair attempt, keep the higher-scoring of the two drafts."""
    first_content, first_report = first
    second_content, second_report = second
    return second if second_report.overall_score >= first_report.overall_score else first
