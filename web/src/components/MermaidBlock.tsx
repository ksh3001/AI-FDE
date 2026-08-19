import { useEffect, useId, useRef, useState } from "react";
import mermaid from "mermaid";

let initialized = false;

function ensureInitialized() {
  if (initialized) return;
  mermaid.initialize({
    startOnLoad: false,
    theme: "dark",
    securityLevel: "strict",
    fontFamily: "EY Interstate, Arial, sans-serif",
    // Without this, render() swallows a parse error and resolves with mermaid's own
    // bomb-icon error graphic instead of rejecting -- our .catch() below never fires
    // and the ugly built-in error SVG gets injected verbatim instead of the contained
    // error box this component is meant to show.
    suppressErrorRendering: true,
  });
  initialized = true;
}

export function MermaidBlock({ code }: { code: string }) {
  const id = useId().replace(/:/g, "-");
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    ensureInitialized();
    let cancelled = false;
    mermaid
      .render(`mermaid-${id}`, code)
      .then(({ svg }) => {
        if (!cancelled && containerRef.current) containerRef.current.innerHTML = svg;
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [code, id]);

  if (error) {
    return (
      <div className="rounded border border-[var(--color-failed)] bg-[var(--color-failed-bg)] p-3 text-sm text-[var(--color-failed)]">
        Diagram failed to render: {error}
      </div>
    );
  }

  return <div ref={containerRef} className="mermaid-diagram my-4 flex justify-center overflow-x-auto" />;
}
