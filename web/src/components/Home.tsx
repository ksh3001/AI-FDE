import { GRID_BG } from "./Header";

const WAYPOINTS: [number, number][] = [
  [0, 130],
  [140, 75],
  [280, 115],
  [440, 45],
  [610, 95],
  [780, 35],
];
const WAYPOINT_PATH = WAYPOINTS.map(([x, y]) => `${x},${y}`).join(" ");

function FdeBackdrop() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0">
      <div className="absolute inset-0" style={GRID_BG} />
      <div className="absolute -left-16 -top-20 h-72 w-72 rounded-full bg-[var(--color-accent)] opacity-[0.10] blur-[100px]" />
      <div className="absolute -right-10 bottom-[-4rem] h-64 w-64 rounded-full bg-[#188CE5] opacity-[0.08] blur-[100px]" />
      <svg viewBox="0 0 800 180" preserveAspectRatio="none" className="absolute inset-0 h-full w-full">
        <polyline points={WAYPOINT_PATH} fill="none" stroke="var(--color-accent)" strokeWidth="1.5" strokeOpacity="0.22" />
        {WAYPOINTS.map(([x, y], i) => (
          <circle key={i} cx={x} cy={y} r="3.5" fill="var(--color-accent)" fillOpacity="0.4" />
        ))}
      </svg>
    </div>
  );
}

type IconName = "journey" | "generator" | "library";

function ModuleIcon({ name }: { name: IconName }) {
  const common = {
    viewBox: "0 0 24 24",
    fill: "none" as const,
    stroke: "currentColor",
    strokeWidth: 1.5,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };
  switch (name) {
    case "journey":
      // A route between two waypoints -- the learning path.
      return (
        <svg {...common} className="h-5 w-5">
          <circle cx="4.5" cy="18" r="2" />
          <circle cx="19.5" cy="6" r="2" />
          <path d="M6.3 16.7 11 11l3 2 4.2-4.7" />
        </svg>
      );
    case "generator":
      // A document being produced -- the pipeline's output.
      return (
        <svg {...common} className="h-5 w-5">
          <path d="M6.5 3h7l4 4v13a1 1 0 0 1-1 1h-10a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
          <path d="M13.5 3v4a1 1 0 0 0 1 1h4" />
          <path d="M9 13h6M9 16.5h6" />
        </svg>
      );
    case "library":
      // An open book -- the prompt library.
      return (
        <svg {...common} className="h-5 w-5">
          <path d="M12 5.5c-1.6-1-4-1.5-6.5-1.5A1.5 1.5 0 0 0 4 5.5v13A1.5 1.5 0 0 1 5.5 17c2.5 0 4.9.5 6.5 1.5" />
          <path d="M12 5.5c1.6-1 4-1.5 6.5-1.5A1.5 1.5 0 0 1 20 5.5v13a1.5 1.5 0 0 0-1.5-1.5c-2.5 0-4.9.5-6.5 1.5" />
          <path d="M12 5.5v13" />
        </svg>
      );
  }
}

interface ModuleTile {
  icon: IconName;
  title: string;
  description: string;
  cta: string;
  onOpen: () => void;
}

function ModuleCard({ icon, title, description, cta, onOpen }: ModuleTile) {
  return (
    <button
      onClick={onOpen}
      className="group flex flex-col items-start gap-3 rounded-xl border border-[var(--color-line-strong)] bg-[var(--color-paper-raised)] p-7 text-left shadow-[var(--shadow-panel)] transition-colors hover:border-[var(--color-accent)]"
    >
      <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--color-accent-soft)] text-[var(--color-accent)]">
        <ModuleIcon name={icon} />
      </span>
      <h2 className="font-sans text-xl font-semibold text-[var(--color-ink)]">{title}</h2>
      <p className="text-sm leading-relaxed text-[var(--color-ink-soft)]">{description}</p>
      <span className="mt-2 font-sans text-sm font-medium text-[var(--color-accent)] group-hover:text-[var(--color-accent-strong)]">
        {cta} →
      </span>
    </button>
  );
}

export function Home({
  onOpenJourney,
  onOpenGenerator,
  onOpenLibrary,
}: {
  onOpenJourney: () => void;
  onOpenGenerator: () => void;
  onOpenLibrary: () => void;
}) {
  return (
    <div className="mx-auto max-w-4xl px-6 py-16">
      <div className="relative overflow-hidden rounded-2xl border border-[var(--color-line)] px-8 py-14 sm:py-20">
        <FdeBackdrop />
        <div className="relative">
          <h1 className="font-sans text-3xl font-semibold text-[var(--color-ink)]">Keystone</h1>
          <p className="mt-2 text-[var(--color-ink-soft)]">Pick where you're starting from.</p>
        </div>
      </div>

      <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <ModuleCard
          icon="journey"
          title="FDE Journey"
          description="The FORGE FDE learning path — ten modules, from operating model through spec-driven delivery — with the topics and reference material behind each stage of this tool."
          cta="Browse the journey"
          onOpen={onOpenJourney}
        />
        <ModuleCard
          icon="generator"
          title="Artefact Generator"
          description="Upload a use case and run it through the reviewed delivery pipeline — Discovery through Solution Proposal — each stage generated, scored, and repaired once if it falls short."
          cta="Start generating"
          onOpen={onOpenGenerator}
        />
        <ModuleCard
          icon="library"
          title="Prompt Library"
          description="The generator prompt behind every stage, in run order — open one to read it in full and copy it."
          cta="Browse the prompts"
          onOpen={onOpenLibrary}
        />
      </div>
    </div>
  );
}
