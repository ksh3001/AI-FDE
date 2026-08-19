"""I3: `depends_on`-based prior-artifact filtering (runner.py's `filter_prior_artifacts`).

Extracted as a pure function specifically so this doesn't need a full RunStore /
ArtifactStore / checkpointer stack to test -- the runner-level wiring (that this
function is actually called with the right arguments) is exercised indirectly by
every test in test_api.py, all of which run against a real pipeline where at least
one stage declares `depends_on` (risk_classification, in config/pipeline.yaml).
"""

from __future__ import annotations

from datetime import datetime, timezone

from ai_fde.core.models import StageArtifact
from ai_fde.core.pipeline.runner import filter_prior_artifacts


def _artifact(stage_id: str) -> StageArtifact:
    return StageArtifact(
        stage_id=stage_id,
        content=f"# {stage_id}",
        prompt_id=f"stage.{stage_id}",
        prompt_version="1.0.0",
        score=90,
        verdict="pass",
        created_at=datetime.now(timezone.utc),
    )


def test_empty_depends_on_returns_every_other_prior_artifact() -> None:
    artifacts = [_artifact("discovery"), _artifact("scqa"), _artifact("architecture")]

    result = filter_prior_artifacts(artifacts, stage_id="decisions", depends_on=[])

    assert [a.stage_id for a in result] == ["discovery", "scqa", "architecture"]


def test_declared_depends_on_excludes_everything_else() -> None:
    artifacts = [_artifact("discovery"), _artifact("scqa"), _artifact("architecture")]

    result = filter_prior_artifacts(
        artifacts, stage_id="decisions", depends_on=["discovery"]
    )

    assert [a.stage_id for a in result] == ["discovery"]


def test_the_stages_own_artifact_is_always_excluded_even_if_self_declared() -> None:
    # Relevant on resume/regenerate, where the stage's own (stale) artifact may
    # still be in the store when this filter runs.
    artifacts = [_artifact("discovery"), _artifact("scqa")]

    result = filter_prior_artifacts(
        artifacts, stage_id="scqa", depends_on=["discovery", "scqa"]
    )

    assert [a.stage_id for a in result] == ["discovery"]


def test_depends_on_naming_a_stage_not_present_yet_is_not_an_error() -> None:
    artifacts = [_artifact("discovery")]

    result = filter_prior_artifacts(
        artifacts, stage_id="architecture", depends_on=["discovery", "domain_model"]
    )

    assert [a.stage_id for a in result] == ["discovery"]
