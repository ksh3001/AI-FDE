import { useEffect } from "react";
import { MarkdownViewer } from "./MarkdownViewer";

export function SkillModal({
  title,
  content,
  onClose,
}: {
  title: string;
  content: string;
  onClose: () => void;
}) {
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-6"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
        className="flex max-h-[85vh] w-full max-w-4xl flex-col overflow-hidden rounded-xl border border-[var(--color-line-strong)] bg-[var(--color-paper-raised)] shadow-[var(--shadow-panel)]"
      >
        <div className="flex items-start justify-between gap-4 border-b border-[var(--color-line)] px-6 py-4">
          <h2 className="font-sans text-lg font-semibold text-[var(--color-ink)]">
            {title}
          </h2>
          <button
            onClick={onClose}
            aria-label="Close"
            className="text-xl leading-none text-[var(--color-ink-faint)] hover:text-[var(--color-ink)]"
          >
            ×
          </button>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-6 py-6">
          <MarkdownViewer content={content} />
        </div>
      </div>
    </div>
  );
}
