from __future__ import annotations

import io
import time
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ai_fde.main import create_app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    # Isolate each test's runs/checkpoints on disk so tests don't collide.
    monkeypatch.setenv("ARTIFACT_STORE_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("CHECKPOINT_DB_PATH", str(tmp_path / "checkpoints.sqlite3"))
    with TestClient(create_app()) as c:
        yield c


def _create_run(client: TestClient, *, mode: str = "auto", content: bytes = b"# Use case\n\nSome content.") -> str:
    response = client.post(
        "/runs",
        data={"mode": mode},
        files={"use_case": ("use_case.md", io.BytesIO(content), "text/markdown")},
    )
    assert response.status_code == 202
    return response.json()["run_id"]


def _poll_until(client: TestClient, run_id: str, predicate, timeout: float = 20.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        body = client.get(f"/runs/{run_id}").json()
        if predicate(body):
            return body
        time.sleep(0.2)
    raise AssertionError(f"timed out waiting for run {run_id} to satisfy predicate; last state: {body}")


def test_prompts_endpoint_lists_the_library(client: TestClient) -> None:
    response = client.get("/prompts")
    assert response.status_code == 200
    ids = {p["id"] for p in response.json()["prompts"]}
    assert "stage.discovery" in ids
    assert "validator.decisions" in ids


def test_create_run_returns_queued(client: TestClient) -> None:
    run_id = _create_run(client)
    body = client.get(f"/runs/{run_id}").json()
    assert body["run_id"] == run_id
    assert body["status"] in ("queued", "parsing", "running", "complete")


def test_get_unknown_run_is_404(client: TestClient) -> None:
    response = client.get("/runs/does-not-exist")
    assert response.status_code == 404


def test_cancel_a_nonexistent_run_is_404(client: TestClient) -> None:
    response = client.post("/runs/does-not-exist/cancel")
    assert response.status_code == 404


def test_auto_mode_runs_all_thirteen_stages_to_completion(client: TestClient) -> None:
    run_id = _create_run(client, mode="auto")

    body = _poll_until(client, run_id, lambda b: b["status"] in ("complete", "failed"), timeout=60.0)

    assert body["status"] == "complete", body
    assert len(body["stages"]) == 13
    assert all(s["verdict"] == "pass" for s in body["stages"])

    artifact = client.get(f"/runs/{run_id}/artifacts/discovery").json()
    assert "Discovery" in artifact["content"]
    assert artifact["attempts"]
    assert artifact["attempts"][0]["validation_report"]["overall_score"] >= 80


def test_bundle_download_for_a_completed_run(client: TestClient, tmp_path: Path) -> None:
    run_id = _create_run(client, mode="auto")
    _poll_until(client, run_id, lambda b: b["status"] in ("complete", "failed"), timeout=60.0)

    response = client.get(f"/runs/{run_id}/bundle")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    zip_path = tmp_path / "bundle.zip"
    zip_path.write_bytes(response.content)
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        manifest_name = next(n for n in names if n.endswith("manifest.json"))
        import json

        manifest = json.loads(zf.read(manifest_name))
        assert manifest["partial"] is False
        assert manifest["run_id"] == run_id
        assert len(manifest["stages"]) == 13
        assert any(n.endswith("01-discovery.md") for n in names)
        assert any(n.endswith("00-README.md") for n in names)
        assert any("/validation/" in n for n in names)
        assert any("/inputs/" in n for n in names)


def test_partial_bundle_for_a_still_running_run(client: TestClient, tmp_path: Path) -> None:
    run_id = _create_run(client, mode="stepwise")
    _poll_until(client, run_id, lambda b: b["status"] == "awaiting_approval")

    response = client.get(f"/runs/{run_id}/bundle")
    assert response.status_code == 200

    zip_path = tmp_path / "partial.zip"
    zip_path.write_bytes(response.content)
    with zipfile.ZipFile(zip_path) as zf:
        import json

        manifest_name = next(n for n in zf.namelist() if n.endswith("manifest.json"))
        manifest = json.loads(zf.read(manifest_name))
        assert manifest["partial"] is True
        assert manifest["status"] == "awaiting_approval"
        assert len(manifest["missing_stages"]) > 0


def test_stepwise_mode_pauses_and_advance_approve_proceeds(client: TestClient) -> None:
    # discovery is a mandatory gate (no auto_approve_on_pass): pauses regardless.
    # scqa has auto_approve_on_pass=true and the fake provider always passes cleanly,
    # so approving discovery skips scqa's own pause and lands on risk_classification --
    # the next mandatory gate.
    run_id = _create_run(client, mode="stepwise")

    body = _poll_until(client, run_id, lambda b: b["status"] == "awaiting_approval")
    assert body["current_stage"] == "discovery"

    response = client.post(f"/runs/{run_id}/advance", json={"action": "approve"})
    assert response.status_code == 200

    body = _poll_until(
        client, run_id, lambda b: b["status"] == "awaiting_approval" and b["current_stage"] == "risk_classification"
    )
    assert [s["stage_id"] for s in body["stages"]] == ["discovery", "scqa"]


def test_auto_approve_on_pass_skips_the_gate_for_a_passing_stage(client: TestClient) -> None:
    """Pins the new stage-level gate policy itself, not just its downstream effect:
    a stage with auto_approve_on_pass=true that passes cleanly is fully recorded
    (needs_review False) without ever pausing for a human decision on it."""
    run_id = _create_run(client, mode="stepwise")
    _poll_until(client, run_id, lambda b: b["status"] == "awaiting_approval")  # discovery gate
    client.post(f"/runs/{run_id}/advance", json={"action": "approve"})

    body = _poll_until(client, run_id, lambda b: b["status"] == "awaiting_approval")
    scqa = next(s for s in body["stages"] if s["stage_id"] == "scqa")
    assert scqa["needs_review"] is False
    assert body["current_stage"] == "risk_classification"


def test_advance_when_not_awaiting_approval_is_409(client: TestClient) -> None:
    run_id = _create_run(client, mode="auto")
    response = client.post(f"/runs/{run_id}/advance", json={"action": "approve"})
    assert response.status_code == 409


def test_cancel_while_awaiting_approval_transitions_immediately(client: TestClient) -> None:
    run_id = _create_run(client, mode="stepwise")
    _poll_until(client, run_id, lambda b: b["status"] == "awaiting_approval")

    response = client.post(f"/runs/{run_id}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_events_stream_replays_from_seq(client: TestClient) -> None:
    run_id = _create_run(client, mode="auto")
    _poll_until(client, run_id, lambda b: b["status"] in ("complete", "failed"))

    response = client.get(f"/runs/{run_id}/events")
    assert response.status_code == 200
    body = response.text
    assert "event: stage_started" in body
    assert "event: stage_generated" in body  # per-node granularity, not just per-stage
    assert "event: stage_validated" in body
    assert "event: stage_complete" in body
    assert "event: run_complete" in body

    # replay from a later seq should return fewer events
    response2 = client.get(f"/runs/{run_id}/events?last_event_id=1000")
    assert response2.status_code == 200


def test_revise_while_run_is_actively_running_is_409(client: TestClient) -> None:
    run_id = _create_run(client, mode="auto")
    response = client.post(f"/runs/{run_id}/revise", json={"stage_id": "architecture"})
    assert response.status_code == 409


def test_revise_unknown_stage_id_is_422(client: TestClient) -> None:
    run_id = _create_run(client, mode="auto")
    _poll_until(client, run_id, lambda b: b["status"] in ("complete", "failed"), timeout=60.0)

    response = client.post(f"/runs/{run_id}/revise", json={"stage_id": "not_a_real_stage"})
    assert response.status_code == 422


def test_revise_a_stage_with_no_artifact_yet_is_422(client: TestClient) -> None:
    run_id = _create_run(client, mode="stepwise")
    _poll_until(client, run_id, lambda b: b["status"] == "awaiting_approval")  # discovery gate

    # Nothing has been accepted yet -- not even discovery, let alone a later stage.
    response = client.post(f"/runs/{run_id}/revise", json={"stage_id": "solution_proposal"})
    assert response.status_code == 422


def test_revise_stage_regenerates_it_and_everything_after_but_not_before(client: TestClient) -> None:
    run_id = _create_run(client, mode="auto")
    first = _poll_until(client, run_id, lambda b: b["status"] in ("complete", "failed"), timeout=60.0)
    assert first["status"] == "complete"

    before = {s["stage_id"]: s for s in first["stages"]}
    assert set(before) == {
        "discovery", "scqa", "risk_classification", "prd", "domain_model", "feature_specs",
        "architecture", "security_model", "decisions", "compliance_controls",
        "technical_design", "lean_dmaic", "solution_proposal",
    }

    # The background task may not have started executing yet by the time this response
    # comes back (asyncio.create_task only schedules it) -- polling for "any terminal
    # status" alone would spuriously match the *first* run's still-unchanged "complete"
    # before the revise has done anything. Poll for real evidence it happened instead:
    # architecture's created_at actually moving.
    response = client.post(f"/runs/{run_id}/revise", json={"stage_id": "architecture"})
    assert response.status_code == 200

    def _revise_took_effect(b: dict) -> bool:
        if b["status"] not in ("complete", "failed"):
            return False
        stages = {s["stage_id"]: s for s in b["stages"]}
        arch = stages.get("architecture")
        return arch is not None and arch["created_at"] != before["architecture"]["created_at"]

    second = _poll_until(client, run_id, _revise_took_effect, timeout=60.0)
    assert second["status"] == "complete", second
    after = {s["stage_id"]: s for s in second["stages"]}
    assert set(after) == set(before)  # still all thirteen -- nothing lost, nothing extra

    untouched = ["discovery", "scqa", "risk_classification", "prd", "domain_model", "feature_specs"]
    regenerated = [
        "architecture", "security_model", "decisions", "compliance_controls",
        "technical_design", "lean_dmaic", "solution_proposal",
    ]
    for stage_id in untouched:
        assert after[stage_id]["created_at"] == before[stage_id]["created_at"], stage_id
    for stage_id in regenerated:
        assert after[stage_id]["created_at"] > before[stage_id]["created_at"], stage_id

    events = client.get(f"/runs/{run_id}/events").text
    assert "event: stage_revised" in events
