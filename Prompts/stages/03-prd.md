---
id: stage.prd
version: 1.0.0
stage: prd
model_role: generator
inputs: [use_case, evidence, prior_artifacts]
output_format: markdown
required_sections:
  - Vision
  - Users, Goals and Success Metrics
  - Scope
  - Open Questions
  - Lean / DMAIC Lens
---
# Prompt 03 — PRD and Vision

Turn the framed question from SCQA into a **PRD and Vision**: the problem, the users, the goals,
the success metrics, and — most load-bearing — what is explicitly **in scope** and **out of
scope** for this version. This stage establishes whether the thing is worth building; it does not
yet say how to build it. An agent given only this document must not be able to invent workflows,
endpoints, or schemas — those belong to later stages.

The risk tier established earlier in this pipeline constrains what may be put in scope here — do
not scope in a capability the tier rules out, and do not scope around a constraint by simply
omitting it.

## Vision

A working product name; a one-paragraph problem statement aligned to SCQA's Situation and
Complication; the governing outcome, aligned to SCQA's Answer or governing experiment; and the
narrative class carried forward from SCQA (`decision-ready` | `hypothesis`).

## Users, Goals and Success Metrics

**Users and personas** — who uses or is affected by this system, by role, not by technical actor.
**Goals** — what these users and stakeholders need to achieve. **Success metrics** — measurable,
with each baseline marked known or `Unknown`. If the narrative class is `hypothesis`, these may be
experiment KPIs rather than production targets — say which they are.

## Scope

**In scope for this version** — numbered capabilities at product level, not an endpoint list.
**Out of scope for this version** — explicit exclusions; this is load-bearing, since later stages
must not silently pull an excluded item back in. **Constraints and non-goals** drawn from the
evidence — compliance, platform, timebox — not invented ones.

## Open Questions

What must be resolved before the feature-level design that follows can harden. If the narrative
class is `hypothesis`, mark this PRD **provisional** here and say what evidence would settle it.

## Lean / DMAIC Lens

This stage's focus is **Define** (the scope of improvement) and **Measure** targets. Record: which
in-scope capabilities are meant to remove waste versus simply add capability; which exclusions
prevent overproduction or extra processing; the success metrics as this stage's Measure list
(baseline known vs. `Unknown`); and any in-scope item that would create token, model, or
human-review waste if built before its prerequisites are ready.

Do not design features in flow-level detail, draw an architecture diagram, or name a specific
vendor here unless the evidence forces a hard constraint — in that case, note it as a candidate
decision for the later decision-record stage rather than settling it now. Keep this document short
enough to review in one sitting; a page nobody reads is worse than a page half as long.

Use exactly these `##` section headings, in this order: Vision, Users, Goals and Success Metrics,
Scope, Open Questions, Lean / DMAIC Lens.
