import { useCallback, useEffect, useRef, useState } from "react";
import { advanceRun, cancelRun, getArtifact, getRun, resumeFailedRun, reviseStage } from "../api";
import { useRunEvents } from "../hooks/useRunEvents";
import type { AttemptSummary, RunSummaryResponse, SSEEvent, StageArtifactResponse, ValidationReport } from "../types";
import { STAGE_LABELS } from "../types";
import { StageRail, computeStagePhase } from "./StageRail";
import { ArtifactPane } from "./ArtifactPane";
import { ValidationPanel } from "./ValidationPanel";
import { RunStatusBar } from "./RunStatusBar";
import { Footer } from "./Footer";

/** Event types that mean "this stage's active work just ended" -- once one of
 * these fires, liveActiveStage should stop pointing at that stage so a stale
 * "generating" badge doesn't linger after the run moves on. */
const STAGE_SETTLED_EVENTS = new Set(["stage_complete", "stage_awaiting", "stage_failed"]);

/** Mirrors ai_fde/api/routes/runs.py's _REVISABLE_STATUSES: a stage may be sent back
 * for revision whenever no background task is currently driving the run. */
const REVISABLE_RUN_STATUSES = new Set(["awaiting_approval", "complete", "failed"]);

interface AwaitingDraft {
  draft: string;
  validation_report: ValidationReport | null;
  needs_review: boolean;
}

export function Workspace({ runId, onBack }: { runId: string; onBack: () => void }) {
  const [run, setRun] = useState<RunSummaryResponse | null>(null);
  const [selectedStage, setSelectedStage] = useState<string | null>(null);
  const [artifact, setArtifact] = useState<StageArtifactResponse | null>(null);
  const [artifactLoading, setArtifactLoading] = useState(false);
  const [livePhaseByStage, setLivePhaseByStage] = useState<Record<string, string>>({});
  const [liveActiveStage, setLiveActiveStage] = useState<string | null>(null);
  const [lastEvent, setLastEvent] = useState<SSEEvent | null>(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [reviseConfirmStage, setReviseConfirmStage] = useState<string | null>(null);
  // The draft content and validation report for a stage sitting at the approval
  // gate -- it isn't in the accepted-artifacts table yet (that only happens on
  // approve), so it exists nowhere else but the stage_awaiting SSE event's payload.
  // Keyed by stage_id so a re-render or a different selection doesn't lose it.
  const [awaitingByStage, setAwaitingByStage] = useState<Record<string, AwaitingDraft>>({});
  const manualSelectionRef = useRef(false);
  const lastCurrentStageRef = useRef<string | null>(null);

  const refreshRun = useCallback(async () => {
    const summary = await getRun(runId);
    setRun(summary);
    return summary;
  }, [runId]);

  useEffect(() => {
    refreshRun().catch(() => undefined);
  }, [refreshRun]);

  useRunEvents(runId, (event) => {
    setLastEvent(event);
    if (event.stage_id) {
      setLivePhaseByStage((prev) => ({ ...prev, [event.stage_id as string]: event.type }));
      setLiveActiveStage(STAGE_SETTLED_EVENTS.has(event.type) ? null : event.stage_id);
    }
    if (event.type === "stage_awaiting" && event.stage_id) {
      const data = event.data as { draft?: string; validation_report?: ValidationReport | null; needs_review?: boolean };
      setAwaitingByStage((prev) => ({
        ...prev,
        [event.stage_id as string]: {
          draft: data.draft ?? "",
          validation_report: data.validation_report ?? null,
          needs_review: data.needs_review ?? false,
        },
      }));
    }
    refreshRun().catch(() => undefined);
  });

  // Follow the active stage automatically; a manual click pins the view until
  // the run actually advances to a different stage.
  useEffect(() => {
    if (!run) return;
    const target = run.current_stage ?? run.stage_ids.find((id) => run.stages.some((s) => s.stage_id === id) === false) ?? run.stage_ids[run.stage_ids.length - 1];
    if (run.current_stage !== lastCurrentStageRef.current) {
      manualSelectionRef.current = false;
      lastCurrentStageRef.current = run.current_stage;
    }
    if (!manualSelectionRef.current && target && target !== selectedStage) {
      setSelectedStage(target);
    } else if (!selectedStage && run.stages.length > 0) {
      setSelectedStage(run.stages[run.stages.length - 1].stage_id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [run]);

  useEffect(() => {
    if (!selectedStage || !run) {
      setArtifact(null);
      return;
    }
    const hasArtifact = run.stages.some((s) => s.stage_id === selectedStage);
    if (!hasArtifact) {
      // Nothing accepted yet -- either there's genuinely nothing (still generating),
      // or it's sitting at the approval gate, in which case the draft comes from the
      // stage_awaiting SSE event (awaitingByStage) instead. Either way, GET
      // /artifacts/{stage} would 404 here since it only serves accepted artifacts.
      setArtifact(null);
      return;
    }
    setArtifactLoading(true);
    getArtifact(runId, selectedStage)
      .then(setArtifact)
      .catch(() => setArtifact(null))
      .finally(() => setArtifactLoading(false));
  }, [selectedStage, run, runId]);

  const handleSelectStage = (stageId: string) => {
    manualSelectionRef.current = true;
    setSelectedStage(stageId);
  };

  const withBusy = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    setActionError(null);
    try {
      await fn();
      await refreshRun();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Action failed.");
    } finally {
      setBusy(false);
    }
  };

  const handleConfirmRevise = () => {
    if (!reviseConfirmStage) return;
    const stageId = reviseConfirmStage;
    setReviseConfirmStage(null);
    withBusy(() => reviseStage(runId, stageId));
  };

  if (!run) {
    return <div className="p-8 text-[var(--color-ink-soft)]">Loading run…</div>;
  }

  const stageTitle = selectedStage ? STAGE_LABELS[selectedStage] ?? selectedStage : "Select a stage";
  const canReviseSelected =
    !!selectedStage &&
    REVISABLE_RUN_STATUSES.has(run.status) &&
    run.stages.some((s) => s.stage_id === selectedStage);
  const reviseDownstreamCount = reviseConfirmStage
    ? run.stage_ids.length - run.stage_ids.indexOf(reviseConfirmStage)
    : 0;
  const isDraftPreview = run.status === "awaiting_approval" && run.current_stage === selectedStage;
  const awaitingDraft = isDraftPreview && selectedStage ? awaitingByStage[selectedStage] : undefined;
  // Deliberately independent of `selectedStage`/`awaitingDraft` above: Footer's
  // approve/edit/regenerate always act on whichever stage is actually awaiting
  // approval, even if the user is currently browsing a different, earlier stage
  // in the rail.
  const currentAwaitingContent =
    run.status === "awaiting_approval" && run.current_stage
      ? awaitingByStage[run.current_stage]?.draft ?? null
      : null;
  const displayedContent = artifact?.content ?? awaitingDraft?.draft ?? null;
  const displayedAttempts: AttemptSummary[] =
    artifact?.attempts ??
    (awaitingDraft
      ? [
          {
            attempt_number: 1,
            content: awaitingDraft.draft,
            prompt_id: "",
            prompt_version: "",
            generator_model: "",
            validation_report: awaitingDraft.validation_report,
          },
        ]
      : []);
  const isSelectedStageActive =
    run.status === "running" && (run.current_stage === selectedStage || liveActiveStage === selectedStage);
  const selectedStagePhase = selectedStage
    ? computeStagePhase(selectedStage, {
        runStatus: run.status,
        currentStage: run.current_stage,
        failedStage: run.failed_stage,
        liveActiveStage,
        livePhaseByStage,
        summary: run.stages.find((s) => s.stage_id === selectedStage),
      })
    : undefined;

  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center justify-between border-b border-[var(--color-line)] px-6 py-3">
        <button onClick={onBack} className="text-sm text-[var(--color-ink-soft)] hover:text-[var(--color-accent)]">
          ← Keystone
        </button>
        <span className="font-mono text-xs text-[var(--color-ink-faint)]">{runId}</span>
      </header>

      {actionError && (
        <div className="border-b border-[var(--color-failed)] bg-[var(--color-failed-bg)] px-6 py-2 text-sm text-[var(--color-failed)]">
          {actionError}
        </div>
      )}
      {run.status === "failed" && (
        <div className="border-b border-[var(--color-failed)] bg-[var(--color-failed-bg)] px-6 py-2 text-sm text-[var(--color-failed)]">
          Run failed{run.failed_stage ? ` at stage ${STAGE_LABELS[run.failed_stage] ?? run.failed_stage}` : ""}
          {run.failure_reason ? `: ${run.failure_reason}` : ""}. Prior stages are intact and browsable.
        </div>
      )}
      {reviseConfirmStage && (
        <div className="flex items-center justify-between gap-3 border-b border-[var(--color-failed)] bg-[var(--color-failed-bg)] px-6 py-2 text-sm text-[var(--color-failed)]">
          <span>
            Revise <strong>{STAGE_LABELS[reviseConfirmStage] ?? reviseConfirmStage}</strong>? This deletes it and
            every stage after it ({reviseDownstreamCount} stage{reviseDownstreamCount === 1 ? "" : "s"} total) so
            they can be regenerated from here.
          </span>
          <span className="flex shrink-0 items-center gap-2">
            <button
              onClick={handleConfirmRevise}
              disabled={busy}
              className="rounded-md bg-[var(--color-failed)] px-3 py-1 text-xs font-medium text-white disabled:opacity-50"
            >
              Confirm revise
            </button>
            <button
              onClick={() => setReviseConfirmStage(null)}
              className="rounded-md border border-[var(--color-failed)] px-3 py-1 text-xs text-[var(--color-failed)]"
            >
              Cancel
            </button>
          </span>
        </div>
      )}

      <RunStatusBar run={run} lastEvent={lastEvent} />

      <div className="grid min-h-0 flex-1 grid-cols-[240px_1fr_320px]">
        <div className="min-h-0 border-r border-[var(--color-line)]">
          <StageRail
            stageIds={run.stage_ids}
            stageSummaries={run.stages}
            runStatus={run.status}
            currentStage={run.current_stage}
            failedStage={run.failed_stage}
            liveActiveStage={liveActiveStage}
            livePhaseByStage={livePhaseByStage}
            selectedStage={selectedStage}
            onSelectStage={handleSelectStage}
          />
        </div>

        <ArtifactPane
          title={stageTitle}
          content={displayedContent}
          phase={selectedStagePhase}
          canRevise={canReviseSelected}
          onRevise={() => selectedStage && setReviseConfirmStage(selectedStage)}
          emptyLabel={
            isDraftPreview
              ? "Generating…"
              : isSelectedStageActive
                ? "This stage is still generating."
                : "Nothing to show yet for this stage."
          }
        />

        <div className="min-h-0 border-l border-[var(--color-line)]">
          <ValidationPanel attempts={displayedAttempts} isLoading={artifactLoading} />
        </div>
      </div>

      <Footer
        run={run}
        busy={busy}
        currentContent={currentAwaitingContent}
        onApprove={() => withBusy(() => advanceRun(runId, { action: "approve" }))}
        onEdit={(content) => withBusy(() => advanceRun(runId, { action: "edit", content }))}
        onRegenerate={(note) => withBusy(() => advanceRun(runId, { action: "regenerate", note }))}
        onCancel={() => withBusy(() => cancelRun(runId))}
        onRetry={() => withBusy(() => resumeFailedRun(runId))}
      />
    </div>
  );
}
