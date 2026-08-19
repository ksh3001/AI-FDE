import clsx from "clsx";
import { STAGE_LABELS, type RunStatus, type StageArtifactSummary } from "../types";

export type StagePhase =
  | "pending"
  | "generating"
  | "validating"
  | "repairing"
  | "awaiting_approval"
  | "passed"
  | "needs_review"
  | "validation_unavailable"
  | "failed";

export const PHASE_META: Record<StagePhase, { label: string; icon: string; fg: string; bg: string }> = {
  pending: { label: "Pending", icon: "○", fg: "var(--color-pending)", bg: "var(--color-pending-bg)" },
  generating: { label: "Generating…", icon: "◐", fg: "var(--color-running)", bg: "var(--color-running-bg)" },
  validating: { label: "Validating…", icon: "◐", fg: "var(--color-validating)", bg: "var(--color-validating-bg)" },
  repairing: { label: "Repairing…", icon: "◐", fg: "var(--color-repairing)", bg: "var(--color-repairing-bg)" },
  awaiting_approval: { label: "Awaiting approval", icon: "◆", fg: "var(--color-awaiting)", bg: "var(--color-awaiting-bg)" },
  passed: { label: "Passed", icon: "✓", fg: "var(--color-passed)", bg: "var(--color-passed-bg)" },
  needs_review: { label: "Needs review", icon: "!", fg: "var(--color-needs-review)", bg: "var(--color-needs-review-bg)" },
  validation_unavailable: { label: "Validation unavailable", icon: "?", fg: "var(--color-needs-review)", bg: "var(--color-needs-review-bg)" },
  failed: { label: "Failed", icon: "✕", fg: "var(--color-failed)", bg: "var(--color-failed-bg)" },
};

/** No provider reports true byte-level progress for an LLM call, so this maps
 * the discrete phase events we do get (generate/validate/repair completing)
 * onto a segmented determinate fill -- more informative than a spinner, honest
 * about not being continuous. */
export const PHASE_PROGRESS: Record<StagePhase, number> = {
  pending: 0,
  generating: 30,
  validating: 60,
  repairing: 78,
  awaiting_approval: 100,
  passed: 100,
  needs_review: 100,
  validation_unavailable: 100,
  failed: 100,
};

const ACTIVE_PHASES: readonly StagePhase[] = ["generating", "validating", "repairing"];

export function StageProgressBar({ phase, className }: { phase: StagePhase; className?: string }) {
  const meta = PHASE_META[phase];
  const percent = PHASE_PROGRESS[phase];
  const isActive = ACTIVE_PHASES.includes(phase);

  if (phase === "pending") return null;

  return (
    <div
      role="progressbar"
      aria-valuenow={percent}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={meta.label}
      className={clsx("h-1 w-full overflow-hidden rounded-full bg-[var(--color-line)]", className)}
    >
      <div
        className={clsx("h-full rounded-full transition-[width] duration-500 ease-out", isActive && "animate-pulse")}
        style={{ width: `${percent}%`, background: meta.fg }}
      />
    </div>
  );
}

export function computeStagePhase(
  stageId: string,
  opts: {
    runStatus: RunStatus;
    currentStage: string | null;
    failedStage: string | null;
    /** The stage the last live SSE event was about -- `current_stage` from the
     * polled run summary only gets set once a run pauses for approval, so
     * without this every stage would read "pending" for the entire time it's
     * actually being generated/validated/repaired. */
    liveActiveStage: string | null;
    livePhaseByStage: Record<string, string>;
    summary: StageArtifactSummary | undefined;
  },
): StagePhase {
  const { runStatus, currentStage, failedStage, liveActiveStage, livePhaseByStage, summary } = opts;

  if (summary) {
    if (summary.validation_unavailable) return "validation_unavailable";
    return summary.needs_review ? "needs_review" : "passed";
  }
  if (runStatus === "failed" && failedStage === stageId) return "failed";

  const isActiveStage = currentStage === stageId || (runStatus === "running" && liveActiveStage === stageId);
  if (isActiveStage) {
    if (runStatus === "awaiting_approval") return "awaiting_approval";
    const live = livePhaseByStage[stageId];
    if (live === "stage_generated") return "validating";
    if (live === "stage_validated") return "repairing";
    if (live === "stage_repaired") return "validating";
    return "generating"; // stage_started, or no live event observed yet
  }
  return "pending";
}

export function StageRail({
  stageIds,
  stageSummaries,
  runStatus,
  currentStage,
  failedStage,
  liveActiveStage,
  livePhaseByStage,
  selectedStage,
  onSelectStage,
}: {
  stageIds: string[];
  stageSummaries: StageArtifactSummary[];
  runStatus: RunStatus;
  currentStage: string | null;
  failedStage: string | null;
  liveActiveStage: string | null;
  livePhaseByStage: Record<string, string>;
  selectedStage: string | null;
  onSelectStage: (stageId: string) => void;
}) {
  const summaryByStage = Object.fromEntries(stageSummaries.map((s) => [s.stage_id, s]));

  return (
    <nav aria-label="Pipeline stages" className="flex h-full flex-col gap-1 overflow-y-auto p-3">
      {stageIds.map((stageId, index) => {
        const summary = summaryByStage[stageId];
        const phase = computeStagePhase(stageId, {
          runStatus,
          currentStage,
          failedStage,
          liveActiveStage,
          livePhaseByStage,
          summary,
        });
        const meta = PHASE_META[phase];
        const clickable = Boolean(summary) || phase === "awaiting_approval";
        const isSelected = selectedStage === stageId;

        return (
          <button
            key={stageId}
            disabled={!clickable}
            onClick={() => clickable && onSelectStage(stageId)}
            className={clsx(
              "flex items-start gap-3 rounded-lg border px-3 py-2.5 text-left transition-colors",
              isSelected ? "border-[var(--color-accent)] bg-[var(--color-accent-soft)]" : "border-transparent",
              clickable ? "cursor-pointer hover:bg-[var(--color-accent-soft)]" : "cursor-default opacity-70",
            )}
          >
            <span
              aria-hidden
              className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold"
              style={{ color: meta.fg, background: meta.bg }}
            >
              {index + 1}
            </span>
            <span className="flex min-w-0 flex-1 flex-col gap-1.5">
              <span className="truncate font-sans text-sm font-medium text-[var(--color-ink)]">
                {STAGE_LABELS[stageId] ?? stageId}
              </span>
              <span className="flex items-center gap-1 text-xs" style={{ color: meta.fg }}>
                <span aria-hidden>{meta.icon}</span>
                {meta.label}
                {summary && <span className="text-[var(--color-ink-faint)]"> · {summary.score}/100</span>}
              </span>
              <StageProgressBar phase={phase} />
            </span>
          </button>
        );
      })}
    </nav>
  );
}
