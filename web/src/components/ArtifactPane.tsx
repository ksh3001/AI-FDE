import { useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";
import { MermaidBlock } from "./MermaidBlock";
import { StageProgressBar, type StagePhase } from "./StageRail";

type ViewMode = "rendered" | "source";

function extractText(node: unknown): string {
  if (typeof node === "string") return node;
  if (Array.isArray(node)) return node.map(extractText).join("");
  if (node && typeof node === "object" && "props" in (node as any)) {
    return extractText((node as any).props?.children);
  }
  return "";
}

const markdownComponents: Components = {
  code(props) {
    const { className, children, ...rest } = props;
    const isMermaid = /language-mermaid/.test(className ?? "");
    if (isMermaid) {
      return <MermaidBlock code={extractText(children).trim()} />;
    }
    return (
      <code className={className} {...rest}>
        {children}
      </code>
    );
  },
};

export function ArtifactPane({
  title,
  content,
  emptyLabel,
  phase,
  canRevise,
  onRevise,
}: {
  title: string;
  content: string | null;
  emptyLabel: string;
  phase?: StagePhase;
  /** True when this stage has an accepted artifact and the run is in a status that
   * allows sending it (and everything after it) back for regeneration -- see
   * ai_fde/api/routes/runs.py's _REVISABLE_STATUSES. */
  canRevise?: boolean;
  onRevise?: () => void;
}) {
  const [mode, setMode] = useState<ViewMode>("rendered");
  const wordCount = useMemo(() => (content ? content.trim().split(/\s+/).length : 0), [content]);
  const showProgress = phase && phase !== "pending" && !content;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="border-b border-[var(--color-line)]">
        <div className="flex items-center justify-between px-6 py-3">
        <div>
          <h2 className="font-sans text-sm font-semibold uppercase tracking-wide text-[var(--color-ink-soft)]">
            {title}
          </h2>
        </div>
        <div className="flex items-center gap-3">
          {content && (
            <span className="text-xs text-[var(--color-ink-faint)]">{wordCount.toLocaleString()} words</span>
          )}
          <div className="flex rounded-md border border-[var(--color-line)] p-0.5 text-xs">
            {(["rendered", "source"] as const).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`rounded px-2.5 py-1 capitalize transition-colors ${
                  mode === m
                    ? "bg-[var(--color-accent)] text-[var(--color-on-accent)]"
                    : "text-[var(--color-ink-soft)] hover:bg-[var(--color-accent-soft)]"
                }`}
              >
                {m}
              </button>
            ))}
          </div>
          {content && (
            <button
              onClick={() => navigator.clipboard.writeText(content)}
              className="rounded border border-[var(--color-line)] px-2.5 py-1 text-xs text-[var(--color-ink-soft)] hover:bg-[var(--color-accent-soft)]"
            >
              Copy
            </button>
          )}
          {content && canRevise && onRevise && (
            <button
              onClick={onRevise}
              title="Send this stage, and every stage after it, back for regeneration."
              className="rounded border border-[var(--color-failed)] px-2.5 py-1 text-xs text-[var(--color-failed)] hover:bg-[var(--color-failed-bg)]"
            >
              Revise…
            </button>
          )}
        </div>
        </div>
        {showProgress && <StageProgressBar phase={phase} />}
      </div>

      <div className="flex-1 overflow-y-auto px-8 py-6">
        {!content ? (
          <p className="text-sm text-[var(--color-ink-faint)]">{emptyLabel}</p>
        ) : mode === "rendered" ? (
          <div className="prose-doc mx-auto">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
              {content}
            </ReactMarkdown>
          </div>
        ) : (
          <pre className="mx-auto max-w-[80ch] overflow-x-auto rounded-md bg-[var(--color-ink)] p-4 font-mono text-sm text-[var(--color-paper)]">
            {content}
          </pre>
        )}
      </div>
    </div>
  );
}
