---
id: shared.house_style
version: 1.0.0
stage: shared
model_role: generator
inputs: []
output_format: markdown
required_sections: []
---
# House style

## Headings

- `#` is reserved for the artifact title (one per document).
- `##` for major sections, `###` for subsections. Do not skip a level.
- Name headings after their content ("Bounded contexts", "Investigation hypotheses"), not after
  the prompt's instruction numbering ("Step 3", "Requirement 2").

## Tables

- Every register (facts, invariants, policies, ubiquitous language, criteria) is a Markdown table,
  one row per item, with a stable ID column where the artifact defines IDs (`INV-*`, `POL-*`, …).
- Keep cell content to a sentence or two; move longer explanation to prose below the table and
  reference the row's ID.

## Diagrams

- C4 and sequence diagrams: fenced ```mermaid``` blocks using `C4Context` / `C4Container` /
  `C4Component` or `sequenceDiagram` syntax so they render live in the workspace.
- Context maps and other DDD diagrams: fenced ```plantuml``` blocks, matching what the domain
  model stage asks for. These are rendered server-side to a PNG before the artifact is ever
  stored, so they display with no client-side dependency, unlike mermaid diagrams above.
- A diagram is not optional decoration where the stage prompt asks for one — code fences with no
  diagram, or prose describing a diagram instead of drawing it, are treated as incomplete.
- **Quote every node and edge label that contains punctuation.** Mermaid's flowchart grammar
  treats a bare `(`, `:`, `,`, `"`, `|`, or `#` inside an unquoted label as the start of a new
  token (often a node-shape delimiter), not literal text — `A -->|note (detail: x)| B` fails to
  parse for exactly this reason, because the parser reads `(detail: x)` as an attempt to open a
  new node shape mid-label. Wrap the whole label in double quotes instead:
  `A -->|"note (detail: x)"| B`, `B["Patient Admission (EHR-sourced)"]`. The same applies to
  PlantUML labels containing parentheses or colons — quote them. When in doubt, quote the label;
  a quoted plain-text label is never wrong, an unquoted one with punctuation usually breaks.
- Prefer a plain label with the detail moved to the surrounding prose over a long label crammed
  with an inline parenthetical — a diagram is easier to both parse and read when each node names
  one thing plainly.
- **C4 diagrams: every element needs its own unique alias, and a boundary must wrap its children
  in braces.** Never reuse an alias for two different elements — declaring `System(Nightingale,
  "...")` and later `Boundary(Nightingale, "...")` with the same alias is an id conflict, not a
  redefinition, and breaks the parse. If an element belongs inside a boundary, declare the
  boundary first and nest the element inside its `{ }`: `System_Boundary(SB, "Label") {
  System(Inner, "...") }`. Never declare an element standalone and then append a same-named,
  brace-less `Boundary(...)` call after the fact — an empty or dangling boundary call is invalid
  C4 syntax, not a harmless annotation.

## Traceability

- When citing the use case or an evidence document, name the file: *"per `intake-notes.pdf`, …"*.
- When citing a prior stage's artifact, name the stage and the specific item: *"per the SCQA
  decision question (Stage 2), …"*.
- Assumptions are written as **Assumption:** followed by the statement, so they are greppable and
  visibly distinct from sourced fact.
- A material fact that is genuinely unknown — not merely unstated — is written as
  `UNKNOWN — <what is missing> · owner: <role> · resolves by: <trigger>`, on its own line. Use
  this instead of inventing a plausible value, and instead of a bare "TBD" that names no owner
  and no resolution path. A validator scores this form as correct; see the validator's scoring
  philosophy.

## Lean / DMAIC lens

Where a stage prompt asks for a `dmaic_lens` (thin, stage-specific) or a full DMAIC workshop, use
the exact heading `## Lean / DMAIC lens` so it renders consistently and stays greppable across
every artifact. Keep it short — the point is a stage-specific read on waste and measurement, not
a restatement of the full DOWNTIME and AI-specific waste registers that belong to the
consolidating workshop stage.

Label every waste finding **observed** or **hypothesized** — never leave the distinction implicit.
A waste noted here without runtime evidence (token, retrieval, model, evaluation, integration,
context, and observability waste are runtime phenomena and cannot be *observed* before a system
runs) is `hypothesized` by construction; write it that way rather than implying more certainty
than the stage can support.
