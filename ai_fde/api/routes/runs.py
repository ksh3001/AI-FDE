"""Run lifecycle routes, wired to the real PipelineRunner and RunStore."""

from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from starlette.background import BackgroundTask

from ai_fde.adapters.storage.run_store import RunNotFoundError, RunStore
from ai_fde.core.pipeline.bundle import build_bundle_zip
from ai_fde.api.schemas import (
    AdvanceRequest,
    AttemptSummary,
    ReviseRequest,
    RunCreateResponse,
    RunSummaryResponse,
    StageArtifactResponse,
    StageArtifactSummary,
)
from ai_fde.core.pipeline.runner import PipelineRunner
from ai_fde.core.pipeline.state import RunMode, TERMINAL_STATUSES
from ai_fde.core.prompts.composer import build_domain_config

router = APIRouter(tags=["runs"])

# A stage may be sent back for revision whenever no background task is currently
# driving the run -- i.e. anywhere a human (or a re-review) could plausibly be looking
# at the run and deciding an earlier stage needs to change. Not "running"/"parsing"/
# "queued": those already have a live task, and yanking an artifact out from under it
# is a race, not a feature.
_REVISABLE_STATUSES = frozenset({"awaiting_approval", "complete", "failed"})


def _store(request: Request) -> RunStore:
    return request.app.state.run_store


def _runner(request: Request) -> PipelineRunner:
    return request.app.state.runner


def _launch(request: Request, coro) -> None:
    """Fire-and-forget a background task, keeping a reference so it isn't GC'd
    mid-execution, and surfacing any unexpected exception instead of losing it
    silently (the one real footgun of asyncio.create_task without awaiting)."""
    tasks: set[asyncio.Task] = request.app.state.background_tasks
    task = asyncio.create_task(coro)
    tasks.add(task)

    def _on_done(t: asyncio.Task) -> None:
        tasks.discard(t)
        if t.cancelled():
            return
        exc = t.exception()
        if exc is not None:
            import logging

            logging.getLogger("ai_fde.runner").exception("background run task failed", exc_info=exc)

    task.add_done_callback(_on_done)


async def _to_summary(store: RunStore, run_id: str) -> RunSummaryResponse:
    record = await store.get_run(run_id)
    artifacts = await store.list_stage_artifacts(run_id)
    pipeline = None  # stage ids come from the request's app.state, filled in by caller
    return RunSummaryResponse(
        run_id=record.run_id,
        status=record.status,
        mode=record.mode,
        current_stage=record.current_stage,
        failed_stage=record.failed_stage,
        failure_reason=record.failure_reason,
        created_at=record.created_at,  # type: ignore[arg-type]
        stage_ids=[],
        stages=[
            StageArtifactSummary(
                stage_id=a.stage_id,
                score=a.score,
                verdict=a.verdict,
                needs_review=a.needs_review,
                validation_unavailable=a.validation_unavailable,
                created_at=a.created_at,
            )
            for a in artifacts
        ],
    )


async def _summary(request: Request, run_id: str) -> RunSummaryResponse:
    try:
        summary = await _to_summary(_store(request), run_id)
    except RunNotFoundError:
        raise HTTPException(status_code=404, detail=f"no run with id {run_id!r}") from None
    summary.stage_ids = [s.id for s in request.app.state.pipeline_config.stages]
    return summary


@router.post("/runs", response_model=RunCreateResponse, status_code=202)
async def create_run(
    request: Request,
    use_case: UploadFile,
    mode: RunMode = Form(...),
    evidence: list[UploadFile] | None = None,
) -> RunCreateResponse:
    run_id = str(uuid.uuid4())
    settings = request.app.state.settings
    inputs_root = settings.artifact_store_dir / run_id

    use_case_dir = inputs_root / "use_case"
    evidence_dir = inputs_root / "evidence"

    def _write_uploads(use_case_bytes: bytes, use_case_name: str, evidence_files: list[tuple[str, bytes]]) -> None:
        use_case_dir.mkdir(parents=True, exist_ok=True)
        (use_case_dir / use_case_name).write_bytes(use_case_bytes)
        if evidence_files:
            evidence_dir.mkdir(parents=True, exist_ok=True)
            for name, content in evidence_files:
                (evidence_dir / name).write_bytes(content)

    use_case_bytes = await use_case.read()
    evidence_payload = [(f.filename or "evidence", await f.read()) for f in (evidence or [])]
    await asyncio.to_thread(_write_uploads, use_case_bytes, use_case.filename or "use_case", evidence_payload)

    store = _store(request)
    await store.create_run(
        run_id=run_id, mode=mode, use_case=None, evidence=[], domain_config=build_domain_config()
    )

    _launch(request, _runner(request).start(run_id))

    return RunCreateResponse(run_id=run_id, status="queued")


@router.get("/runs/{run_id}", response_model=RunSummaryResponse)
async def get_run(run_id: str, request: Request) -> RunSummaryResponse:
    return await _summary(request, run_id)


@router.get("/runs/{run_id}/events")
async def stream_events(run_id: str, request: Request) -> StreamingResponse:
    store = _store(request)
    try:
        await store.get_run(run_id)
    except RunNotFoundError:
        raise HTTPException(status_code=404, detail=f"no run with id {run_id!r}") from None

    last_seq_header = request.headers.get("last-event-id") or request.query_params.get("last_event_id")
    last_seq = int(last_seq_header) if last_seq_header else 0

    async def _generator():
        seq = last_seq
        while True:
            events = await store.list_events_after(run_id, seq)
            for event in events:
                seq = event["seq"]
                payload = {"stage_id": event["stage_id"], **event["data"]}
                yield f"id: {event['seq']}\nevent: {event['type']}\ndata: {json.dumps(payload)}\n\n"

            record = await store.get_run(run_id)
            if record.status in TERMINAL_STATUSES and not events:
                break
            await asyncio.sleep(0.3)

    return StreamingResponse(_generator(), media_type="text/event-stream")


@router.post("/runs/{run_id}/advance", response_model=RunSummaryResponse)
async def advance_run(run_id: str, body: AdvanceRequest, request: Request) -> RunSummaryResponse:
    store = _store(request)
    try:
        record = await store.get_run(run_id)
    except RunNotFoundError:
        raise HTTPException(status_code=404, detail=f"no run with id {run_id!r}") from None

    if record.status != "awaiting_approval":
        raise HTTPException(status_code=409, detail=f"run is {record.status!r}, not awaiting_approval")

    stage_id = record.current_stage
    assert stage_id is not None

    action: dict[str, object] = {"action": body.action}
    if body.action == "edit":
        if body.content is None:
            raise HTTPException(status_code=422, detail="action=edit requires content")
        action["content"] = body.content
    elif body.action == "regenerate":
        latest = await store.get_latest_event(run_id, stage_id=stage_id, type="stage_awaiting")
        count = latest["data"].get("regenerate_count", 0) if latest else 0
        if count >= 5:
            raise HTTPException(
                status_code=400,
                detail="regenerate cap (5) reached for this stage -- edit the draft directly instead",
            )
        action["note"] = body.note

    _launch(request, _runner(request).resume(run_id, action))

    return await _summary(request, run_id)


@router.post("/runs/{run_id}/cancel", response_model=RunSummaryResponse)
async def cancel_run(run_id: str, request: Request) -> RunSummaryResponse:
    store = _store(request)
    try:
        record = await store.get_run(run_id)
    except RunNotFoundError:
        raise HTTPException(status_code=404, detail=f"no run with id {run_id!r}") from None

    if record.status == "awaiting_approval":
        # No background task is live -- safe to transition immediately.
        await store.transition(run_id, "cancelled")
    elif record.status == "running":
        # A background task is live -- it checks this flag at the next node
        # boundary and transitions itself. Never cancel mid-LLM-call.
        _runner(request).request_cancel(run_id)
    else:
        raise HTTPException(status_code=409, detail=f"cannot cancel a run that is {record.status!r}")

    return await _summary(request, run_id)


@router.post("/runs/{run_id}/resume", response_model=RunSummaryResponse)
async def resume_failed_run(run_id: str, request: Request) -> RunSummaryResponse:
    store = _store(request)
    try:
        record = await store.get_run(run_id)
    except RunNotFoundError:
        raise HTTPException(status_code=404, detail=f"no run with id {run_id!r}") from None

    if record.status != "failed":
        raise HTTPException(status_code=409, detail=f"run is {record.status!r}, not failed")

    await store.transition(run_id, "running")
    _launch(request, _runner(request).retry_failed(run_id))

    return await _summary(request, run_id)


@router.post("/runs/{run_id}/revise", response_model=RunSummaryResponse)
async def revise_stage(run_id: str, body: ReviseRequest, request: Request) -> RunSummaryResponse:
    store = _store(request)
    try:
        record = await store.get_run(run_id)
    except RunNotFoundError:
        raise HTTPException(status_code=404, detail=f"no run with id {run_id!r}") from None

    if record.status not in _REVISABLE_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"run is {record.status!r}; a stage can only be revised while "
            f"{sorted(_REVISABLE_STATUSES)}",
        )

    pipeline = request.app.state.pipeline_config
    if body.stage_id not in {s.id for s in pipeline.stages}:
        raise HTTPException(status_code=422, detail=f"unknown stage id {body.stage_id!r}")

    if await store.get_stage_artifact(run_id, body.stage_id) is None:
        raise HTTPException(
            status_code=422,
            detail=f"stage {body.stage_id!r} has no accepted artifact yet -- nothing to revise",
        )

    _launch(request, _runner(request).revise_stage(run_id, body.stage_id))

    return await _summary(request, run_id)


@router.get("/runs/{run_id}/bundle")
async def get_bundle(run_id: str, request: Request) -> FileResponse:
    store = _store(request)
    try:
        await store.get_run(run_id)
    except RunNotFoundError:
        raise HTTPException(status_code=404, detail=f"no run with id {run_id!r}") from None

    settings = request.app.state.settings
    tmp_path, download_name = await build_bundle_zip(
        run_id,
        store=store,
        pipeline=request.app.state.pipeline_config,
        registry=request.app.state.prompt_registry,
        inputs_root=settings.artifact_store_dir,
    )

    return FileResponse(
        tmp_path,
        media_type="application/zip",
        filename=download_name,
        background=BackgroundTask(tmp_path.unlink, missing_ok=True),
    )


@router.get("/runs/{run_id}/artifacts/{stage_id}", response_model=StageArtifactResponse)
async def get_artifact(run_id: str, stage_id: str, request: Request) -> StageArtifactResponse:
    store = _store(request)
    try:
        await store.get_run(run_id)
    except RunNotFoundError:
        raise HTTPException(status_code=404, detail=f"no run with id {run_id!r}") from None

    artifact = await store.get_stage_artifact(run_id, stage_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail=f"no artifact for stage {stage_id!r} yet on run {run_id!r}")

    attempts_raw = await store.get_stage_attempts(run_id, stage_id) or []
    return StageArtifactResponse(
        stage_id=artifact.stage_id,
        content=artifact.content,
        prompt_id=artifact.prompt_id,
        prompt_version=artifact.prompt_version,
        score=artifact.score,
        verdict=artifact.verdict,
        needs_review=artifact.needs_review,
        validation_unavailable=artifact.validation_unavailable,
        created_at=artifact.created_at,
        attempts=[
            AttemptSummary(
                attempt_number=i + 1,
                content=a["content"],
                prompt_id=a["prompt_id"],
                prompt_version=a["prompt_version"],
                generator_model=a["generator_model"],
                validation_report=a["validation_report"],
            )
            for i, a in enumerate(attempts_raw)
        ],
    )
