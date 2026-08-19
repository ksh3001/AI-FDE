export const GRID_BG = {
  backgroundImage:
    "linear-gradient(var(--color-line) 1px, transparent 1px), linear-gradient(90deg, var(--color-line) 1px, transparent 1px)",
  backgroundSize: "32px 32px",
};

const NAV_LINKS = [
  { hash: "#/journey", label: "Journey" },
  { hash: "#/generator", label: "Generator" },
  { hash: "#/library", label: "Prompts" },
];

function BrandMark() {
  return (
    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--color-accent)]">
      <svg viewBox="0 0 24 24" className="h-4 w-4" fill="var(--color-on-accent)">
        <path d="M9 3h6l4 9-4 9H9l-4-9Z" />
      </svg>
    </span>
  );
}

export function Header() {
  return (
    <header className="relative overflow-hidden border-b border-[var(--color-line)]">
      <div aria-hidden className="absolute inset-0" style={GRID_BG} />
      <div
        aria-hidden
        className="pointer-events-none absolute -top-24 right-0 h-72 w-72 rounded-full bg-[var(--color-accent)] opacity-[0.08] blur-[100px]"
      />

      <div className="relative mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
        <a href="#/" className="flex items-center gap-2.5">
          <BrandMark />
          <span className="font-sans text-lg font-bold tracking-tight text-[var(--color-ink)]">Keystone</span>
        </a>
        <nav className="hidden gap-6 font-sans text-sm text-[var(--color-ink-soft)] sm:flex">
          {NAV_LINKS.map((link) => (
            <a key={link.hash} href={link.hash} className="transition-colors hover:text-[var(--color-accent)]">
              {link.label}
            </a>
          ))}
        </nav>
      </div>
    </header>
  );
}
