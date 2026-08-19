---
id: stage.scqa
version: 2.0.0
stage: scqa
model_role: generator
inputs: [use_case, evidence, prior_artifacts]
output_format: markdown
required_sections:
  - Narrative Class and Evidence Boundary
  - SCQA Narrative
  - Minto Pyramid
  - Framing Handoff Pack
  - Lean / DMAIC Lens
---
# Prompt 02 — SCQA and Minto Pyramid

Turn Discovery's evidence into a clear, audience-ready decision narrative. Lead with the answer
(Minto): structure the story as **Situation → Complication → Question → Answer** (SCQA), and
support the answer with MECE key points and evidence — never the reverse order.

Respect Discovery's declared **framing mode**:

- `decision-ready` — the narrative supports a capability decision; the pyramid rests mainly on
  facts and derivations.
- `hypothesis` — the narrative frames a **testable recommendation**; the Answer is an experiment
  or learning plan, not a locked build mandate.

## Narrative Class and Evidence Boundary

State at the top: the **narrative class** (`decision-ready` | `hypothesis`), which must match
Discovery's framing mode unless new evidence genuinely upgraded it — if it changed, say what
changed and why. State the **evidence boundary** — what this narrative is allowed to claim — and,
if the class is `hypothesis`, the top blocking items from Discovery's acquisition backlog that
keep it there.

## SCQA Narrative

**Situation** — current state of operations, relevant facts, concise context; prefer facts and
derivations, label assumptions. **Complication** — the compound problem across every dimension
that applies (operational, technical, financial, regulatory, human, environmental, security, data,
or domain-specific — use what the evidence actually supports, not a checklist filled by rote).
**Question** — exactly one bounded decision or engineering question that must be answered; not a
restated problem statement. **Answer** — in `decision-ready` mode, a capability-level
recommendation **without** preselecting architecture, vendor, or model; in `hypothesis` mode, a
capability-level **recommended experiment**: what to test, what would falsify it, and what
evidence must be acquired before locking a decision.

Also state: desired outcomes and what "good" looks like; audience, decision horizon, evidence
boundary, and authority boundary; measurable outcomes with baselines marked known vs. unknown; and
explicit exclusions — what this decision does **not** cover.

## Minto Pyramid

Present the Answer as a pyramid: the **governing answer** (one clear recommendation, or the
governing experiment in hypothesis mode) at the top; **MECE key supporting points** beneath it
(typically three to seven — mutually exclusive, collectively exhaustive); and, under each point,
the support — citing Discovery's facts and derivations by name. In `hypothesis` mode, assumptions
are allowed under a point only if labeled and tied to an acquisition-backlog item.

## Framing Handoff Pack

The decision question, locked for the design stages that follow (or provisional, if `hypothesis`);
success metrics later stages can use, with missing baselines noted; open questions that block
design and must be resolved or explicitly assumed; and whether downstream artifacts must be marked
**provisional** as a result of this stage's class.

## Lean / DMAIC Lens

This stage's focus is **Define** (the improvement problem and its success measures). Record: what
waste or rework the Complication itself describes, named against DOWNTIME or AI-specific waste
where it's clear; which success metrics are Measure targets for the later consolidation stage
(known vs. `Unknown` baseline); what must *not* be automated yet because a baseline is missing (a
`hypothesis` framing implies Measure-first); and one sentence on how the Answer reduces waste
without introducing new model, token, or process waste of its own.

Use exactly these `##` section headings, in this order: Narrative Class and Evidence Boundary,
SCQA Narrative, Minto Pyramid, Framing Handoff Pack, Lean / DMAIC Lens.
