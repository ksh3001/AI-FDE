import clsx from "clsx";
import type { RunSummaryResponse, SSEEvent } from "../types";
import { STAGE_LABELS } from "../types";

export type StatusTone = "idle" | "active" | "success" | "error";

const TONE_COLOR: Record<StatusTone, string> = {
  idle: "var(--color-ink-faint)",
  active: "var(--color-running)",
  success: "var(--color-passed)",
  error: "var(--color-failed)",
};

function label(stageId: string | null): string {
  return stageId ? (STAGE_LABELS[stageId] ?? stageId) : "";
}

/** Turns the run's polled status plus the last SSE event into one human
 * sentence -- the polled status alone can't distinguish "generating" from
 * "validating" from "repairing", since the backend only reports a
 * current_stage once a run pauses for approval. */
export function describeRunStatus(
  run: RunSummaryResponse,
  lastEvent: SSEEvent | null,
): { text: string; tone: StatusTone } {
  if (run.status === "failed") {
    return {
      text: `Run failed at ${label(run.failed_stage)}${run.failure_reason ? ` — ${run.failure_reason}` : ""}.`,
      tone: "error",
    };
  }
  if (run.status === "cancelled") return { text: "Run cancelled.", tone: "idle" };
  if (run.status === "complete") {
    return { text: "All stages complete — solution pack ready to download.", tone: "success" };
  }
  if (run.status === "awaiting_approval") {
    return { text: `${label(run.current_stage)} draft ready for review.`, tone: "success" };
  }
  if (run.status === "queued") return { text: "Queued — starting shortly…", tone: "active" };
  if (run.status === "parsing") return { text: "Parsing the uploaded input…", tone: "active" };

  if (!lastEvent) return { text: "Starting the pipeline…", tone: "active" };

  const stage = label(lastEvent.stage_id);
  switch (lastEvent.type) {
    case "stage_started":
      return { text: `Generating ${stage}…`, tone: "active" };
    case "stage_generated":
      return { text: `${stage} drafted — validating…`, tone: "active" };
    case "stage_validated": {
      const score = lastEvent.data.score as number | null | undefined;
      const verdict = lastEvent.data.verdict as string | null | undefined;
      return verdict === "fail"
        ? { text: `${stage} scored ${score ?? "?"}/100 — repairing…`, tone: "active" }
        : { text: `${stage} validated (${score ?? "?"}/100)…`, tone: "active" };
    }
    case "stage_repaired":
      return { text: `${stage} repaired — re-validating…`, tone: "active" };
    case "stage_complete": {
      const score = lastEvent.data.score as number | null | undefined;
      const needsReview = lastEvent.data.needs_review as boolean | undefined;
      return {
        text: `${stage} accepted (${score ?? "?"}/100)${needsReview ? " — flagged for review" : ""}.`,
        tone: "success",
      };
    }
    default:
      return { text: "Working…", tone: "active" };
  }
}

export function RunStatusBar({ run, lastEvent }: { run: RunSummaryResponse; lastEvent: SSEEvent | null }) {
  const { text, tone } = describeRunStatus(run, lastEvent);
  const color = TONE_COLOR[tone];

  return (
    <div className="border-b border-[var(--color-line)] bg-[var(--color-paper-raised)] px-6 py-2.5">
      <div className="flex items-center gap-2 text-sm" style={{ color }}>
        <span
          aria-hidden
          className={clsx("h-1.5 w-1.5 shrink-0 rounded-full", tone === "active" && "animate-pulse")}
          style={{ background: color }}
        />
        <span>{text}</span>
      </div>
      {tone === "active" && (
        <div role="progressbar" aria-label={text} className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-[var(--color-line)]">
          <div className="h-full w-full animate-pulse rounded-full" style={{ background: color, opacity: 0.6 }} />
        </div>
      )}
    </div>
  );
}
