---
id: stage.lean_dmaic
version: 1.0.0
stage: lean_dmaic
model_role: generator
inputs: [use_case, evidence, prior_artifacts]
output_format: markdown
required_sections:
  - Lens Roll-Up
  - DMAIC Plan
  - DOWNTIME Waste Register
  - AI-Specific Waste Register
  - Build Constraints
  - Structural Reopen Gate
---
# Prompt 09 — Lean and DMAIC Consolidation

Consolidate the Lean/DMAIC operating spine that has been running as a thin lens through every
stage so far. Every prior stage already produced its own `## Lean / DMAIC Lens` section — **do not
ignore them.** Start from those, and from Discovery's early waste signals, then produce the full
DOWNTIME and AI-specific waste registers and a complete DMAIC plan. This is the stage where the
whole chain's improvement story gets said once, plainly, instead of scattered across eleven thin
paragraphs.

**Scarce-data rule:** if Discovery's baselines are Missing or Partial, or the narrative class
carried from SCQA is `hypothesis`, this stage's Improve plan is **Measure-first** —
instrumentation, sampling, and evidence acquisition outrank any new capability.

## Lens Roll-Up

A table of every prior stage's `## Lean / DMAIC Lens` section — Discovery, SCQA, risk
classification, PRD, domain model, feature specs, architecture, security model, decisions,
compliance controls, technical design — with each one's DMAIC focus and its top finding. Merge and
de-duplicate the wastes already named across them. Name any stage whose lens was thin or missing
outright — a gap here is itself a finding, not something to paper over.

Deepen into the full registers below from this roll-up; do not restart from a blank page as if the
prior eleven stages said nothing.

## DMAIC Plan

**Define** — the improvement problem and scope, aligned to SCQA's Question and Answer and the
PRD's scope. **Measure** — current-state and target metrics, drawn from Discovery and the prior
lenses wherever possible, with every unknown baseline listed explicitly and each target tied to a
feature's acceptance criteria where one applies. **Analyze** — root causes and gaps, linked to the
evidence register and the waste findings below; mark any analysis that rests on an assumption.
**Improve** — the changes that would remove waste, and which of them this pack already reflects
versus which are explicitly deferred. **Control** — standards, governance, monitoring ownership,
and revisit triggers, reusing the decision records' own revisit triggers rather than inventing
new ones.

If baselines are unknown or the narrative class is `hypothesis`: put instrumentation, sampling, and
evidence acquisition at the top of Improve; do not schedule scale-out of agents, retrieval, or
automation ahead of the capacity to measure it; and cross-link every such Improve item to the
relevant entry in Discovery's evidence acquisition backlog.

## DOWNTIME Waste Register

One row per waste — Defects, Overproduction, Waiting, Non-utilised talent, Transportation,
Inventory, Motion, Extra processing — each with: where it is observed in the current state and/or
the proposed design, `observed` vs `hypothesized`, its impact, and the action that would eliminate
or simplify it.

## AI-Specific Waste Register

Assess and plan an action for each: token waste, retrieval waste, model waste, human-review waste,
evaluation waste, integration waste, context waste, observability waste.

## Build Constraints

For whoever implements this pack: which items are **must-resolve before implementation begins**,
which are **acceptable to resolve during implementation**, and which are **accepted as residual
risk** — each named, not just bucketed.

## Structural Reopen Gate

If any Improve action above requires a change to the C4 map, a decision record, or a technical
contract, do not let the pack proceed silently. State: **reopen required?** `yes` | `no`; if
`yes`, which of the architecture, security-model, decisions, or technical-design stages must be
revisited, and which specific decision records or contracts need updating; the **status flip** —
which decision records move to `proposed` or `superseded`, and whether the architecture review
should return to `conditional`; and the **gate decision** — `blocked` (stop; the reopen must
complete and the affected stages be re-accepted before this pack is considered ready) or `cleared`
(no reopen was needed, or one was completed and is documented above). **The solution-proposal
stage that follows this one requires `cleared`.**

Do not claim a waste is fixed without a Measure baseline or an explicit, labeled assumption. Do
not expand the architecture casually — if waste removal needs a structural change, both update the
relevant decision record and set the reopen gate accordingly. Prefer removing waste over adding
agents or models. Under evidence scarcity, do not prioritise feature scale over instrumentation.
Do not hand off to the next stage while this gate reads `blocked`.

Use exactly these `##` section headings, in this order: Lens Roll-Up, DMAIC Plan, DOWNTIME Waste
Register, AI-Specific Waste Register, Build Constraints, Structural Reopen Gate.
