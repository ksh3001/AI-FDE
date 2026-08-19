"""Drives a run from queued through complete/failed/cancelled.

Shared between the initial background kickoff (POST /runs) and every resume
path (POST /runs/{id}/advance, /resume) -- both funnel through
`_process_stages`, which is what makes "approve stage N -> stage N+1
auto-generates and pauses again" fall out naturally rather than needing
separate code paths per state-machine edge.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langgraph.types import Command

from ai_fde.adapters.parsers import select_parser
from ai_fde.adapters.storage.run_store import RunStore
from ai_fde.core.models import Attempt, LLMUsage, StageArtifact
from ai_fde.core.pipeline.config import PipelineConfig
from ai_fde.core.pipeline.diagrams import render_diagrams_in_markdown
from ai_fde.core.pipeline.graph import build_stage_graph
from ai_fde.core.ports import ArtifactStore, DiagramRenderer, LLMClient
from ai_fde.core.prompts.registry import PromptRegistry
from ai_fde.core.settings import Settings


class RunCancelled(Exception):
    pass


def filter_prior_artifacts(
    artifacts: list[StageArtifact], *, stage_id: str, depends_on: list[str]
) -> list[StageArtifact]:
    """Never includes the stage's own artifact (it hasn't been accepted yet, or is
    being resumed/regenerated). `depends_on` empty means "every other prior
    artifact" -- the pipeline's original behaviour, and what a stage that hasn't
    declared its dependencies still gets, so declaring `depends_on` is opt-in
    narrowing, never a behaviour change for a stage that omits it."""
    artifacts = [a for a in artifacts if a.stage_id != stage_id]
    if depends_on:
        artifacts = [a for a in artifacts if a.stage_id in depends_on]
    return artifacts


class PipelineRunner:
    def __init__(
        self,
        *,
        store: RunStore,
        artifact_store: ArtifactStore,
        llm_client: LLMClient,
        diagram_renderer: DiagramRenderer,
        registry: PromptRegistry,
        pipeline: PipelineConfig,
        checkpointer: Any,
        settings: Settings,
        inputs_root: Path,
    ) -> None:
        self._store = store
        self._artifact_store = artifact_store
        self._llm_client = llm_client
        self._diagram_renderer = diagram_renderer
        self._registry = registry
        self._pipeline = pipeline
        self._checkpointer = checkpointer
        self._settings = settings
        self._inputs_root = inputs_root
        self._cancel_flags: dict[str, bool] = {}

    def request_cancel(self, run_id: str) -> None:
        self._cancel_flags[run_id] = True

    async def start(self, run_id: str) -> None:
        """Background-task entry point for a freshly-created run."""
        await self._parse_inputs(run_id)
        await self._process_stages(run_id)

    async def resume(self, run_id: str, action: dict[str, Any]) -> None:
        """Background-task entry point for POST /runs/{id}/advance."""
        record = await self._store.get_run(run_id)
        stage_id = record.current_stage
        assert stage_id is not None
        await self._store.transition(run_id, "running")
        await self._process_stages(run_id, resume_stage_id=stage_id, resume_action=action)

    async def retry_failed(self, run_id: str) -> None:
        """Background-task entry point for POST /runs/{id}/resume (a failed run)."""
        record = await self._store.get_run(run_id)
        if record.use_case is None:
            await self._parse_inputs(run_id)
        else:
            await self._store.transition(run_id, "running")
        await self._process_stages(run_id)

    async def revise_stage(self, run_id: str, stage_id: str) -> None:
        """Background-task entry point for POST /runs/{id}/revise.

        Sends an already-accepted stage -- and, since everything after it was built on
        context this stage is about to change, every stage after it too -- back for
        regeneration. This is the backward loop several v2 stages assume exists: an
        architecture review, a compliance gate, or the Lean/DMAIC structural-reopen
        check can all conclude an earlier stage needs to change, not just this one.

        Both the accepted artifact *and* the stage's own LangGraph checkpoint thread
        are cleared before re-running -- clearing only the artifact would leave stale
        checkpoint history on the same thread_id, and the fresh run must not be able
        to inherit anything from the one it's replacing.
        """
        stages_to_clear = [
            s.id for s in self._pipeline.stages if s.order >= self._stage_order(stage_id)
        ]
        await self._store.delete_stage_artifacts(run_id, stages_to_clear)
        for sid in stages_to_clear:
            await self._checkpointer.adelete_thread(f"{run_id}:{sid}")

        await self._store.transition(run_id, "running", current_stage=stage_id)
        await self._store.append_event(
            run_id, type="stage_revised", stage_id=stage_id,
            data={"cleared_stages": stages_to_clear},
        )
        await self._process_stages(run_id)

    def _stage_order(self, stage_id: str) -> int:
        return next(s.order for s in self._pipeline.stages if s.id == stage_id)

    async def _parse_inputs(self, run_id: str) -> None:
        record = await self._store.get_run(run_id)
        await self._store.transition(run_id, "parsing")
        await self._store.append_event(run_id, type="run_parsing", stage_id=None, data={})

        try:
            use_case_dir = self._inputs_root / run_id / "use_case"
            evidence_dir = self._inputs_root / run_id / "evidence"
            use_case_files = list(use_case_dir.glob("*")) if use_case_dir.is_dir() else []
            if not use_case_files:
                raise ValueError("no use case file was uploaded")
            use_case_path = use_case_files[0]
            parser = select_parser(use_case_path.name)
            use_case_doc = await parser.parse(use_case_path.read_bytes(), use_case_path.name)

            evidence_docs = []
            for path in sorted(evidence_dir.glob("*")) if evidence_dir.is_dir() else []:
                evidence_docs.append(await select_parser(path.name).parse(path.read_bytes(), path.name))

        except Exception as exc:  # noqa: BLE001 - parse failures end the run, never partially
            await self._store.transition(run_id, "failed", failure_reason=f"parse error: {exc}")
            await self._store.append_event(
                run_id, type="stage_failed", stage_id=None, data={"reason": str(exc)}
            )
            return

        await self._store.set_parsed_documents(run_id, use_case=use_case_doc, evidence=evidence_docs)
        await self._store.transition(run_id, "running")

    async def _process_stages(
        self,
        run_id: str,
        *,
        resume_stage_id: str | None = None,
        resume_action: dict[str, Any] | None = None,
    ) -> None:
        record = await self._store.get_run(run_id)
        if record.use_case is None:
            return  # parse failed; nothing to run

        for stage in self._pipeline.stages:
            if self._cancel_flags.pop(run_id, False):
                await self._store.transition(run_id, "cancelled")
                await self._store.append_event(run_id, type="run_cancelled", stage_id=None, data={})
                return

            existing = await self._store.get_stage_artifact(run_id, stage.id)
            if existing is not None and stage.id != resume_stage_id:
                continue  # already accepted -- never re-run a completed stage

            prior_artifacts = await self._store.list_stage_artifacts(run_id)
            prior_artifacts = filter_prior_artifacts(
                prior_artifacts, stage_id=stage.id, depends_on=stage.depends_on
            )

            try:
                graph = build_stage_graph(
                    llm_client=self._llm_client,
                    registry=self._registry,
                    pipeline=self._pipeline,
                    stage=stage,
                    generator_prompt_id=stage.generator,
                    use_case=record.use_case,
                    evidence=record.evidence,
                    prior_artifacts=prior_artifacts,
                    settings=self._settings,
                    domain_config=record.domain_config,
                    checkpointer=self._checkpointer,
                )
                thread_config = {"configurable": {"thread_id": f"{run_id}:{stage.id}"}}

                if stage.id == resume_stage_id and resume_action is not None:
                    graph_input: Any = Command(resume=resume_action)
                    resume_stage_id = None  # only the first stage in this call resumes
                else:
                    await self._store.append_event(run_id, type="stage_started", stage_id=stage.id, data={})
                    graph_input = {
                        "mode": record.mode,
                        "threshold": self._settings.validation_threshold,
                        "max_repair_attempts": self._settings.max_repair_attempts,
                    }

                interrupted = False
                async for chunk in graph.astream(graph_input, config=thread_config, stream_mode="updates"):
                    if "__interrupt__" in chunk:
                        interrupted = True
                        continue
                    await self._emit_node_event(run_id, stage_id=stage.id, chunk=chunk)

                result = (await graph.aget_state(thread_config)).values
            except Exception as exc:  # noqa: BLE001 - an unhandled stage error must never leave
                # the run silently parked in "running" forever with nothing left to act on it.
                await self._store.transition(
                    run_id, "failed", failed_stage=stage.id, failure_reason=f"stage error: {exc}"
                )
                await self._store.append_event(
                    run_id, type="stage_failed", stage_id=stage.id, data={"reason": str(exc)}
                )
                return

            if interrupted:
                await self._store.transition(run_id, "awaiting_approval", current_stage=stage.id)
                await self._store.append_event(
                    run_id,
                    type="stage_awaiting",
                    stage_id=stage.id,
                    data={
                        "draft": result.get("draft", ""),
                        "validation_report": result.get("validation_report"),
                        "needs_review": result.get("needs_review", False),
                        "regenerate_count": result.get("regenerate_count", 0),
                    },
                )
                return

            await self._finalize_stage(run_id, stage_id=stage.id, generator_prompt_id=stage.generator, result=result)

        await self._store.transition(run_id, "complete", current_stage=None)
        await self._store.append_event(run_id, type="run_complete", stage_id=None, data={})

    async def _emit_node_event(self, run_id: str, *, stage_id: str, chunk: dict[str, Any]) -> None:
        """Translates one LangGraph node-completion chunk into the granular
        started/generated/validated/repaired SSE events the UI shows per stage."""
        for node_name, update in chunk.items():
            if node_name == "generate":
                await self._store.append_event(
                    run_id, type="stage_generated", stage_id=stage_id,
                    data={"draft_preview": (update.get("draft") or "")[:280]},
                )
            elif node_name == "validate":
                report = update.get("validation_report")
                await self._store.append_event(
                    run_id, type="stage_validated", stage_id=stage_id,
                    data={
                        "score": report["overall_score"] if report else None,
                        "verdict": report["verdict"] if report else None,
                        "validation_unavailable": update.get("validation_unavailable", False),
                    },
                )
            elif node_name == "repair":
                await self._store.append_event(
                    run_id, type="stage_repaired", stage_id=stage_id,
                    data={"draft_preview": (update.get("draft") or "")[:280]},
                )

    async def _finalize_stage(
        self, run_id: str, *, stage_id: str, generator_prompt_id: str, result: dict[str, Any]
    ) -> None:
        pipeline_stage = next(s for s in self._pipeline.stages if s.id == stage_id)
        report = result.get("validation_report")
        content = await render_diagrams_in_markdown(
            result["draft"],
            renderer=self._diagram_renderer,
            artifact_store=self._artifact_store,
            run_id=run_id,
            stage_id=stage_id,
        )
        artifact = StageArtifact(
            stage_id=stage_id,
            content=content,
            prompt_id=generator_prompt_id,
            prompt_version=self._registry.get(generator_prompt_id).front_matter.version,
            score=report["overall_score"] if report else 0,
            verdict=report["verdict"] if report else "fail",
            needs_review=result.get("needs_review", False),
            validation_unavailable=result.get("validation_unavailable", False),
            created_at=datetime.now(timezone.utc),
        )
        attempts = [
            Attempt(
                stage_id=stage_id,
                attempt_number=i + 1,
                content=a["content"],
                prompt_id=a["prompt_id"],
                prompt_version=self._registry.get(a["prompt_id"]).front_matter.version,
                generator_model=a["generator_model"],
                usage=LLMUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0, cost_usd=0.0),
                validation_report=a.get("validation_report"),
                created_at=datetime.now(timezone.utc),
            )
            for i, a in enumerate(result.get("attempts_log", []))
        ]

        await self._store.save_stage_artifact(run_id, artifact, attempts)
        await self._artifact_store.save_artifact(run_id, stage_id, pipeline_stage.artifact_filename, artifact.content)
        await self._store.append_event(
            run_id,
            type="stage_complete",
            stage_id=stage_id,
            data={"score": artifact.score, "needs_review": artifact.needs_review, "repaired": result.get("repaired", False)},
        )
