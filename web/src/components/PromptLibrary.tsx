import { useCallback, useEffect, useState } from "react";
import { getPrompt, listPrompts } from "../api";
import type { PromptDetail, PromptSummary } from "../types";
import { STAGE_LABELS } from "../types";

function PromptCard({ index, prompt, onOpen }: { index: number; prompt: PromptSummary; onOpen: () => void }) {
  return (
    <button
      onClick={onOpen}
      className="flex flex-col items-start gap-2 rounded-lg border border-[var(--color-line-strong)] bg-[var(--color-paper-raised)] p-5 text-left shadow-[var(--shadow-panel)] transition-colors hover:border-[var(--color-accent)]"
    >
      <span className="font-mono text-xs text-[var(--color-ink-faint)]">
        {String(index + 1).padStart(2, "0")}
      </span>
      <h3 className="font-sans text-base font-semibold text-[var(--color-ink)]">
        {prompt.title ?? STAGE_LABELS[prompt.stage] ?? prompt.stage}
      </h3>
      <span className="font-mono text-xs text-[var(--color-ink-soft)]">v{prompt.version}</span>
    </button>
  );
}

function PromptModal({ prompt, detail, loading, error, onClose }: {
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

export function PromptLibrary() {
  const [prompts, setPrompts] = useState<PromptSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [details, setDetails] = useState<Record<string, PromptDetail>>({});
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  useEffect(() => {
    listPrompts()
      .then((all) => setPrompts(all.filter((p) => p.id.startsWith("stage."))))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load the prompt library."));
  }, []);

  const openPrompt = useCallback(
    (id: string) => {
      setSelectedId(id);
      if (details[id]) return;
      setDetailLoading(true);
      setDetailError(null);
      getPrompt(id)
        .then((detail) => setDetails((prev) => ({ ...prev, [id]: detail })))
        .catch((err) => setDetailError(err instanceof Error ? err.message : "Failed to load this prompt."))
        .finally(() => setDetailLoading(false));
    },
    [details],
  );

  const selected = prompts.find((p) => p.id === selectedId) ?? null;

  return (
    <div className="mx-auto max-w-5xl px-6 py-16">
      <h1 className="font-sans text-3xl font-semibold text-[var(--color-ink)]">Prompt Library</h1>
      <p className="mt-2 text-[var(--color-ink-soft)]">
        The generator prompt behind every stage of the pipeline, in run order. Open one to read it
        in full and copy it.
      </p>

      {error && <p className="mt-6 text-sm text-[var(--color-failed)]">{error}</p>}

      <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {prompts.map((prompt, i) => (
          <PromptCard key={prompt.id} index={i} prompt={prompt} onOpen={() => openPrompt(prompt.id)} />
        ))}
      </div>

      {selected && (
        <PromptModal
          prompt={selected}
          detail={details[selected.id] ?? null}
          loading={detailLoading && !details[selected.id]}
          error={detailError}
          onClose={() => setSelectedId(null)}
        />
      )}
    </div>
  );
}
