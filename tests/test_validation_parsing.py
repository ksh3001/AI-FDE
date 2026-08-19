"""Real validator models routinely wrap their JSON in markdown fences or add a
sentence of prose despite explicit instructions not to -- this is what surfaced
as 'validation unavailable' against a real Azure OpenAI deployment. Pinning the
extraction behaviour directly so it can't regress silently."""

from __future__ import annotations

import json

from ai_fde.core.pipeline.graph import _try_parse_report

VALID_REPORT = {
    "overall_score": 85,
    "verdict": "pass",
    "criteria": [{"name": "completeness", "score": 85, "weight": 1.0, "comment": "fine"}],
    "issues": [],
    "repair_instructions": "",
}


def test_parses_bare_json() -> None:
    report, error = _try_parse_report(json.dumps(VALID_REPORT))
    assert error is None
    assert report is not None
    assert report.overall_score == 85


def test_parses_json_wrapped_in_markdown_fence() -> None:
    raw = f"```json\n{json.dumps(VALID_REPORT)}\n```"
    report, error = _try_parse_report(raw)
    assert error is None
    assert report is not None


def test_parses_json_wrapped_in_bare_fence_no_language_tag() -> None:
    raw = f"```\n{json.dumps(VALID_REPORT)}\n```"
    report, error = _try_parse_report(raw)
    assert error is None
    assert report is not None


def test_parses_json_with_leading_and_trailing_prose() -> None:
    raw = f"Here is my assessment:\n\n{json.dumps(VALID_REPORT)}\n\nLet me know if you have questions."
    report, error = _try_parse_report(raw)
    assert error is None
    assert report is not None


def test_genuinely_non_json_response_fails_with_a_clear_error() -> None:
    report, error = _try_parse_report("I cannot evaluate this draft right now.")
    assert report is None
    assert error is not None
    assert "not valid JSON" in error


def test_json_missing_required_fields_fails_schema_validation_not_silently() -> None:
    raw = json.dumps({"overall_score": 85})
    report, error = _try_parse_report(raw)
    assert report is None
    assert "schema" in (error or "")
