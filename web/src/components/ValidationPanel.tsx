import { useState } from "react";
import type { AttemptSummary, ValidationIssue } from "../types";

const SEVERITY_ORDER: ValidationIssue["severity"][] = ["critical", "major", "minor"];
const SEVERITY_META: Record<ValidationIssue["severity"], { fg: string; bg: string; label: string }> = {
  critical: { fg: "var(--color-failed)", bg: "var(--color-failed-bg)", label: "Critical" },
  major: { fg: "var(--color-repairing)", bg: "var(--color-repairing-bg)", label: "Major" },
  minor: { fg: "var(--color-needs-review)", bg: "var(--color-needs-review-bg)", label: "Minor" },
};

function ScoreBadge({ score }: { score: number }) {
  const color = score >= 80 ? "var(--color-passed)" : score >= 60 ? "var(--color-needs-review)" : "var(--color-failed)";
  return (
    <div className="flex items-baseline gap-1">
      <span className="font-sans text-4xl font-bold" style={{ color }}>
        {score}
      </span>
      <span className="text-sm text-[var(--color-ink-faint)]">/100</span>
    </div>
  );
}

export function ValidationPanel({
  attempts,
  isLoading,
}: {
  attempts: AttemptSummary[];
  isLoading: boolean;
}) {
  const [selected, setSelected] = useState(0);

  if (isLoading) {
    return <div className="p-6 text-sm text-[var(--color-ink-faint)]">Loading validation…</div>;
  }
  if (attempts.length === 0) {
    return <div className="p-6 text-sm text-[var(--color-ink-faint)]">No validation yet for this stage.</div>;
  }

  const activeIndex = Math.min(selected, attempts.length - 1);
  const attempt = attempts[activeIndex];
  const report = attempt.validation_report;

  return (
    <div className="flex h-full flex-col overflow-y-auto p-6">
      <h2 className="mb-3 font-sans text-sm font-semibold uppercase tracking-wide text-[var(--color-ink-soft)]">
        Validation
      </h2>

      {attempts.length > 1 && (
        <div className="mb-4 flex rounded-md border border-[var(--color-line)] p-0.5 text-xs">
          {attempts.map((a, i) => (
            <button
              key={a.attempt_number}
              onClick={() => setSelected(i)}
              className={`flex-1 rounded px-2 py-1 ${
                i === activeIndex ? "bg-[var(--color-accent)] text-[var(--color-on-accent)]" : "text-[var(--color-ink-soft)]"
              }`}
            >
              Attempt {a.attempt_number}
              {a.validation_report ? ` · ${a.validation_report.overall_score}` : ""}
            </button>
          ))}
        </div>
      )}

      {attempts.length > 1 && attempts[0].validation_report && attempts[1]?.validation_report && (
        <p className="mb-4 rounded-md bg-[var(--color-accent-soft)] px-3 py-2 text-xs text-[var(--color-accent-strong)]">
          {attempts[1].validation_report.overall_score >= attempts[0].validation_report.overall_score
            ? `Improved from ${attempts[0].validation_report.overall_score} to ${attempts[1].validation_report.overall_score} after review.`
            : `The original draft (${attempts[0].validation_report.overall_score}) scored higher than the repair (${attempts[1].validation_report.overall_score}) and was kept.`}
        </p>
      )}

      {!report ? (
        <p className="text-sm text-[var(--color-needs-review)]">
          Validation was unavailable for this attempt — the validator's response could not be parsed even after a
          retry.
        </p>
      ) : (
        <>
          <div className="mb-1 flex items-center gap-3">
            <ScoreBadge score={report.overall_score} />
            <span
              className="rounded-full px-2.5 py-0.5 text-xs font-medium capitalize"
              style={{
                color: report.verdict === "pass" ? "var(--color-passed)" : "var(--color-needs-review)",
                background: report.verdict === "pass" ? "var(--color-passed-bg)" : "var(--color-needs-review-bg)",
              }}
            >
              {report.verdict}
            </span>
          </div>

          <div className="mt-5 flex flex-col gap-3">
            {report.criteria.map((c) => (
              <div key={c.name}>
                <div className="mb-1 flex items-center justify-between text-xs">
                  <span className="font-medium capitalize text-[var(--color-ink)]">{c.name}</span>
                  <span className="text-[var(--color-ink-faint)]">
                    {c.score} · weight {c.weight}
                  </span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-[var(--color-line)]">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${c.score}%`,
                      background: c.score >= 80 ? "var(--color-passed)" : c.score >= 60 ? "var(--color-needs-review)" : "var(--color-failed)",
                    }}
                  />
                </div>
                {c.comment && <p className="mt-1 text-xs text-[var(--color-ink-faint)]">{c.comment}</p>}
              </div>
            ))}
          </div>

          {report.issues.length > 0 && (
            <div className="mt-6">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-soft)]">
                Issues
              </h3>
              <div className="flex flex-col gap-2">
                {[...report.issues]
                  .sort((a, b) => SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity))
                  .map((issue, i) => {
                    const meta = SEVERITY_META[issue.severity];
                    return (
                      <div key={i} className="rounded-md border border-[var(--color-line)] p-2.5 text-xs">
                        <span
                          className="mb-1 inline-block rounded px-1.5 py-0.5 font-medium"
                          style={{ color: meta.fg, background: meta.bg }}
                        >
                          {meta.label}
                        </span>
                        <p className="text-[var(--color-ink)]">
                          <strong>{issue.location}:</strong> {issue.problem}
                        </p>
                        <p className="mt-1 text-[var(--color-ink-soft)]">Fix: {issue.fix}</p>
                      </div>
                    );
                  })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
