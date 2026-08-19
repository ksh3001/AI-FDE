import { useEffect, useState } from "react";
import type { RunSummaryResponse } from "../types";
import { bundleUrl } from "../api";

function useElapsed(createdAt: string, stop: boolean) {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    const start = new Date(createdAt).getTime();
    setElapsed(Math.max(0, Date.now() - start));
    if (stop) return;
    const id = setInterval(() => setElapsed(Date.now() - start), 1000);
    return () => clearInterval(id);
  }, [createdAt, stop]);
  const totalSeconds = Math.floor(elapsed / 1000);
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function Footer({
  run,
  busy,
  currentContent,
  onApprove,
  onEdit,
  onRegenerate,
  onCancel,
  onRetry,
}: {
  run: RunSummaryResponse;
  busy: boolean;
  /** The draft currently awaiting approval, so "Edit and approve" starts from what's
   * actually there instead of a blank textarea a user could accidentally approve
   * empty. Null while the draft hasn't loaded yet. */
  currentContent: string | null;
  onApprove: () => void;
  onEdit: (content: string) => void;
  onRegenerate: (note: string) => void;
  onCancel: () => void;
  onRetry: () => void;
}) {
  const [showEdit, setShowEdit] = useState(false);
  const [editText, setEditText] = useState("");
  const [showRegenerate, setShowRegenerate] = useState(false);
  const [note, setNote] = useState("");

  const isTerminal = run.status === "complete" || run.status === "cancelled" || run.status === "failed";
  const elapsed = useElapsed(run.created_at, isTerminal);
  const doneCount = run.stages.length;

  return (
    <div className="border-t border-[var(--color-line)] bg-[var(--color-paper-raised)] px-6 py-3">
      {showEdit && (
        <div className="mb-3 flex flex-col gap-2">
          <textarea
            className="h-40 w-full rounded-md border border-[var(--color-line)] bg-[var(--color-paper)] p-3 font-mono text-sm"
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
            placeholder="Edit the artifact content, then approve..."
          />
          <div className="flex gap-2">
            <button
              className="rounded-md bg-[var(--color-accent)] px-3 py-1.5 text-sm text-[var(--color-on-accent)]"
              onClick={() => {
                onEdit(editText);
                setShowEdit(false);
              }}
            >
              Save edit and approve
            </button>
            <button
              className="rounded-md border border-[var(--color-line)] px-3 py-1.5 text-sm"
              onClick={() => setShowEdit(false)}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {showRegenerate && (
        <div className="mb-3 flex flex-col gap-2">
          <input
            className="w-full rounded-md border border-[var(--color-line)] bg-[var(--color-paper)] p-2 text-sm"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="What should change? (e.g. 'cite the evidence file by name for each claim')"
          />
          <div className="flex gap-2">
            <button
              className="rounded-md bg-[var(--color-accent)] px-3 py-1.5 text-sm text-[var(--color-on-accent)]"
              onClick={() => {
                onRegenerate(note);
                setShowRegenerate(false);
                setNote("");
              }}
            >
              Regenerate with this note
            </button>
            <button
              className="rounded-md border border-[var(--color-line)] px-3 py-1.5 text-sm"
              onClick={() => setShowRegenerate(false)}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-4 text-xs text-[var(--color-ink-soft)]">
          <span className="rounded-full bg-[var(--color-accent-soft)] px-2.5 py-1 font-medium capitalize text-[var(--color-accent-strong)]">
            {run.mode} mode
          </span>
          <span>Elapsed {elapsed}</span>
          <span className="flex items-center gap-2">
            {doneCount}/{run.stage_ids.length} stages accepted
            <span
              role="progressbar"
              aria-valuenow={doneCount}
              aria-valuemin={0}
              aria-valuemax={run.stage_ids.length}
              className="h-1.5 w-20 overflow-hidden rounded-full bg-[var(--color-line)]"
            >
              <span
                className="block h-full rounded-full bg-[var(--color-accent)] transition-[width] duration-500 ease-out"
                style={{ width: `${(doneCount / run.stage_ids.length) * 100}%` }}
              />
            </span>
          </span>
          {run.failure_reason && <span className="text-[var(--color-failed)]">{run.failure_reason}</span>}
        </div>

        <div className="flex items-center gap-2">
          {run.status === "running" || run.status === "parsing" || run.status === "queued" ? (
            <button
              onClick={onCancel}
              className="rounded-md border border-[var(--color-line)] px-3 py-1.5 text-sm text-[var(--color-ink-soft)] hover:bg-[var(--color-failed-bg)] hover:text-[var(--color-failed)]"
            >
              Cancel run
            </button>
          ) : null}

          {run.status === "awaiting_approval" && (
            <>
              <button
                onClick={onCancel}
                className="rounded-md border border-[var(--color-line)] px-3 py-1.5 text-sm text-[var(--color-ink-soft)]"
              >
                Cancel run
              </button>
              <button
                onClick={() => setShowRegenerate((v) => !v)}
                disabled={busy}
                className="rounded-md border border-[var(--color-line)] px-3 py-1.5 text-sm text-[var(--color-ink)] disabled:opacity-50"
              >
                Regenerate with a note
              </button>
              <button
                onClick={() => {
                  if (!showEdit) setEditText(currentContent ?? "");
                  setShowEdit((v) => !v);
                }}
                disabled={busy || !currentContent}
                title={!currentContent ? "Waiting for the draft to load…" : undefined}
                className="rounded-md border border-[var(--color-line)] px-3 py-1.5 text-sm text-[var(--color-ink)] disabled:opacity-50"
              >
                Edit and approve
              </button>
              <button
                onClick={onApprove}
                disabled={busy}
                className="rounded-md bg-[var(--color-accent)] px-4 py-1.5 text-sm font-medium text-[var(--color-on-accent)] disabled:opacity-50"
              >
                Approve and continue
              </button>
            </>
          )}

          {run.status === "failed" && (
            <button
              onClick={onRetry}
              className="rounded-md bg-[var(--color-accent)] px-4 py-1.5 text-sm font-medium text-[var(--color-on-accent)]"
            >
              Retry stage {run.failed_stage ?? ""}
            </button>
          )}

          {(run.status === "complete" || run.status === "cancelled" || run.status === "failed") && (
            <a
              href={bundleUrl(run.run_id)}
              className="rounded-md bg-[var(--color-accent)] px-4 py-1.5 text-sm font-medium text-[var(--color-on-accent)]"
            >
              Download solution pack{run.status !== "complete" ? " (partial)" : ""}
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
