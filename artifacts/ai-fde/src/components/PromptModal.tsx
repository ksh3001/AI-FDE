import { useEffect, useState } from "react";
import type { PromptDetail, PromptSummary } from "../types";
import { STAGE_LABELS } from "../types";

export function PromptModal({ prompt, detail, loading, error, onClose }: {
  prompt: PromptSummary;
  detail: PromptDetail | null;
  loading: boolean;
  error: string | null;
  onClose: () => void;
}) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  const handleCopy = async () => {
    if (!detail) return;
    await navigator.clipboard.writeText(detail.body);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-6"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
        className="flex max-h-[85vh] w-full max-w-3xl flex-col overflow-hidden rounded-xl border border-[var(--color-line-strong)] bg-[var(--color-paper-raised)] shadow-[var(--shadow-panel)]"
      >
        <div className="flex items-start justify-between gap-4 border-b border-[var(--color-line)] px-6 py-4">
          <div>
            <h2 className="font-sans text-lg font-semibold text-[var(--color-ink)]">
              {prompt.title ?? STAGE_LABELS[prompt.stage] ?? prompt.stage}
            </h2>
            <p className="mt-1 font-mono text-xs text-[var(--color-ink-faint)]">
              {prompt.id} · v{prompt.version}
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="text-xl leading-none text-[var(--color-ink-faint)] hover:text-[var(--color-ink)]"
          >
            ×
          </button>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-6 py-4">
          {loading && <p className="text-sm text-[var(--color-ink-faint)]">Loading…</p>}
          {error && <p className="text-sm text-[var(--color-failed)]">{error}</p>}
          {detail && (
            <pre className="whitespace-pre-wrap break-words font-mono text-xs leading-relaxed text-[var(--color-ink)]">
              {detail.body}
            </pre>
          )}
        </div>

        <div className="flex items-center justify-end gap-2 border-t border-[var(--color-line)] px-6 py-3">
          <button
            onClick={handleCopy}
            disabled={!detail}
            className="rounded-md bg-[var(--color-accent)] px-4 py-1.5 text-sm font-medium text-[var(--color-on-accent)] disabled:opacity-50"
          >
            {copied ? "Copied!" : "Copy prompt"}
          </button>
        </div>
      </div>
    </div>
  );
}
