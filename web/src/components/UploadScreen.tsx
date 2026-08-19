import { useCallback, useRef, useState } from "react";
import clsx from "clsx";
import { createRun } from "../api";

const ACCEPTED_USE_CASE = [".pptx", ".pdf", ".md", ".zip"];

function FileChip({ name, onRemove, tone }: { name: string; onRemove: () => void; tone: "primary" | "evidence" }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs",
        tone === "primary"
          ? "border-[var(--color-accent)] bg-[var(--color-accent-soft)] text-[var(--color-accent-strong)]"
          : "border-[var(--color-line)] bg-[var(--color-paper)] text-[var(--color-ink-soft)]",
      )}
    >
      {name}
      <button onClick={onRemove} aria-label={`Remove ${name}`} className="text-[var(--color-ink-faint)] hover:text-[var(--color-failed)]">
        ×
      </button>
    </span>
  );
}

export function UploadScreen({ onRunCreated }: { onRunCreated: (runId: string) => void }) {
  const [useCase, setUseCase] = useState<File | null>(null);
  const [evidence, setEvidence] = useState<File[]>([]);
  const [dragging, setDragging] = useState(false);
  const [submitting, setSubmitting] = useState<"auto" | "stepwise" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const acceptDrop = useCallback((files: FileList) => {
    const list = Array.from(files);
    if (!list.length) return;
    setError(null);

    if (!useCase) {
      const [first, ...rest] = list;
      setUseCase(first);
      setEvidence((prev) => [...prev, ...rest]);
    } else {
      setEvidence((prev) => [...prev, ...list]);
    }
  }, [useCase]);

  const handleSubmit = async (mode: "auto" | "stepwise") => {
    if (!useCase) {
      setError("Drop or choose a use case file first.");
      return;
    }
    setSubmitting(mode);
    setError(null);
    try {
      const { run_id } = await createRun(useCase, evidence, mode);
      onRunCreated(run_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start the run.");
      setSubmitting(null);
    }
  };

  return (
    <div className="mx-auto max-w-2xl px-6 py-16">
      <h1 className="font-sans text-3xl font-semibold text-[var(--color-ink)]">Artefact Generator</h1>
      <p className="mt-2 text-[var(--color-ink-soft)]">
        Upload a use case — or a zipped repo to reverse-engineer from code — and it runs through the reviewed
        delivery pipeline, Discovery through Solution Proposal, each stage generated, scored, and repaired once
        if it falls short.
      </p>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          acceptDrop(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        className={clsx(
          "mt-8 flex min-h-[180px] cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed p-8 text-center transition-colors",
          dragging ? "border-[var(--color-accent)] bg-[var(--color-accent-soft)]" : "border-[var(--color-line-strong)]",
        )}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          className="hidden"
          accept={[...ACCEPTED_USE_CASE, ".txt"].join(",")}
          onChange={(e) => e.target.files && acceptDrop(e.target.files)}
        />
        <p className="font-medium text-[var(--color-ink)]">Drop the use case file or a zipped repo here, or click to browse</p>
        <p className="text-xs text-[var(--color-ink-faint)]">
          First file dropped is the use case ({ACCEPTED_USE_CASE.join(", ")}); any additional files become evidence
        </p>
      </div>

      {(useCase || evidence.length > 0) && (
        <div className="mt-4 flex flex-wrap gap-2">
          {useCase && <FileChip name={useCase.name} tone="primary" onRemove={() => setUseCase(null)} />}
          {evidence.map((f, i) => (
            <FileChip
              key={`${f.name}-${i}`}
              name={f.name}
              tone="evidence"
              onRemove={() => setEvidence((prev) => prev.filter((_, j) => j !== i))}
            />
          ))}
        </div>
      )}

      {error && <p className="mt-3 text-sm text-[var(--color-failed)]">{error}</p>}

      <div className="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <button
          onClick={() => handleSubmit("auto")}
          disabled={submitting !== null}
          className="rounded-lg bg-[var(--color-accent)] px-4 py-3 text-left text-[var(--color-on-accent)] shadow-[var(--shadow-panel)] disabled:opacity-60"
        >
          <span className="block font-semibold">Run all stages</span>
          <span className="block text-xs text-[var(--color-on-accent)]/70">One click, full run to a downloadable ZIP.</span>
        </button>
        <button
          onClick={() => handleSubmit("stepwise")}
          disabled={submitting !== null}
          className="rounded-lg border border-[var(--color-line-strong)] px-4 py-3 text-left text-[var(--color-ink)] disabled:opacity-60"
        >
          <span className="block font-semibold">Run step by step</span>
          <span className="block text-xs text-[var(--color-ink-soft)]">
            Review, edit, or steer each stage before the next one runs.
          </span>
        </button>
      </div>
      {submitting && <p className="mt-3 text-sm text-[var(--color-ink-faint)]">Starting the run…</p>}
    </div>
  );
}
