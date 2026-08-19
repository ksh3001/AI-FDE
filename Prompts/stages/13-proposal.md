---
id: stage.solution_proposal
version: 1.0.0
stage: solution_proposal
model_role: generator
inputs: [use_case, evidence, prior_artifacts]
output_format: markdown
required_sections:
  - Evidence Confidence and Problem Statement
  - Governing Answer
  - Scope and Target Operating Workflow
  - Measurable Outcomes and Feature Summary
  - Domain Ownership
  - Target Architecture and Key Decisions
  - Technical and Data Strategy
  - Safety, Security and Governance Controls
  - Evidence Acquisition and Data-Access Plan
  - Lean Summary
  - Adoption, Roadmap and Delivery Assumptions
  - Residual Risks and Sponsor Decisions
  - Lean / DMAIC Lens
---
# Prompt 13 — Final Solution Proposal

Synthesize the whole pipeline into one proposal a sponsor can act on: the SCQA story, the PRD
scope, the feature summary, the domain ownership, the target architecture, the decision trade-offs,
the technical contracts, the security and compliance controls, and the Lean/DMAIC path. This
pipeline produces a **specification pack, not a built system** — every claim in this proposal must
be labeled `specified` (this pack fully specifies it), `assumed` (asserted with a labeled
assumption behind it), or `unknown` (an open question a sponsor must resolve). Never let a
specified design read as a verified result — nothing here has been built or tested yet, and the
proposal must not imply otherwise anywhere, not just in a caveat at the end.

If the engagement ran in `hypothesis` or `provisional` mode at any stage, this proposal must lead
with **what is unknown**, the evidence-acquisition plan, and the sponsor data-access decisions —
not only the solution vision. A sponsor who reads only the first section should already understand
how much of this is settled versus still open.

## Evidence Confidence and Problem Statement

The narrative class and artifact-status history across the pipeline — where it stayed
`decision-ready`/`stable` and where it went `hypothesis`/`provisional`, and why. Then the problem
statement itself: SCQA's Situation and Complication, compressed for a sponsor audience, with any
assumption-heavy part labeled as such.

## Governing Answer

The Minto top of the pyramid — the governing recommendation, or the governing experiment if the
engagement stayed in `hypothesis` mode — with its MECE supporting reasons summarized, not
reproduced in full.

## Scope and Target Operating Workflow

The PRD's in-scope and out-of-scope for this version, and how the solution fits day-to-day
operations, including where a human is in the loop and why.

## Measurable Outcomes and Feature Summary

Outcomes from SCQA, the PRD, and the Lean/DMAIC consolidation stage's Measure targets, with every
unknown baseline called out rather than smoothed over. Then a feature-by-feature summary: what was
specified and what remains `unknown` — never claim a feature was verified, since nothing in this
pipeline builds or tests it.

## Domain Ownership

Bounded contexts, their owners, and the decision rights that sit with each — drawn directly from
the domain-model stage.

## Target Architecture and Key Decisions

The C4 views and how they meet the stated requirements, marked `provisional` if the underlying
domain model or architecture never left that status. The consequential decision records and what
was sacrificed by choosing as they did — not every decision record, the ones that would actually
change a sponsor's read of the plan.

## Technical and Data Strategy

API, data-model, and NFR highlights from the technical-design stage, and the data and integration
strategy — sources, flows, anti-corruption boundaries, and prohibited write paths.

## Safety, Security and Governance Controls

The non-functional guarantees this design makes: what the security-model and compliance-controls
stages established, including the risk tier, the human-oversight requirement, and the compliance
gate's status (`cleared` / `conditional` / `blocked`) — a `blocked` gate must be visible here, not
buried.

## Evidence Acquisition and Data-Access Plan

What must be obtained next, from whom, and what it unblocks — pulled forward from Discovery's
acquisition backlog and every stage that added to it.

## Lean Summary

The top wastes this design removes versus what remains open, drawn from the Lean/DMAIC
consolidation stage's registers; the Control approach; and which items are Measure-first because a
baseline is still unknown.

## Adoption, Roadmap and Delivery Assumptions

How people would work differently under this design; a phased roadmap that front-loads discovery
and instrumentation where evidence was scarce; and the assumptions that must remain true for the
plan to hold.

## Residual Risks and Sponsor Decisions

Risks accepted or deferred, each with an owner where one exists. Then the decisions a sponsor must
actually make — data access, subject-matter-expert time, source-of-truth authority, scope changes,
and whether to commit to implementing this pack at all. Be specific and actionable; a decision a
sponsor cannot act on by reading this section has not been asked properly.

## Lean / DMAIC Lens

This stage's focus is the executive **Control** story — what this design improves, what remains
open, and what to fund next. Record: the top wastes this design removes versus what is still open,
from the Lean/DMAIC consolidation stage's registers; the Measure baselines still `Unknown` that
only a sponsor decision can unlock; the control owners named by the compliance-controls and
Lean/DMAIC stages; and a recommendation for the next Define–Measure–Analyze–Improve–Control loop —
without implying continuous improvement will simply happen on its own; name who would own it.

Throughout, label every material claim `specified`, `assumed`, or `unknown` — do not let a reader
come away believing anything in this pack has been demonstrated in a running system. Do not
introduce a major new architecture choice here without flagging that it reopens the architecture
or decision-record stages. Do not bury a residual risk or a data gap in appendix-only language if
it would block moving forward. Keep the governing answer visible near the top, per Minto — do not
bury the recommendation under process.

Use exactly these `##` section headings, in this order: Evidence Confidence and Problem Statement,
Governing Answer, Scope and Target Operating Workflow, Measurable Outcomes and Feature Summary,
Domain Ownership, Target Architecture and Key Decisions, Technical and Data Strategy, Safety,
Security and Governance Controls, Evidence Acquisition and Data-Access Plan, Lean Summary,
Adoption, Roadmap and Delivery Assumptions, Residual Risks and Sponsor Decisions, Lean / DMAIC
Lens.
