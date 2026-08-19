---
id: stage.discovery
version: 2.0.0
stage: discovery
model_role: generator
inputs: [use_case, evidence]
output_format: markdown
required_sections:
  - Repository and Evidence Map
  - Constraints Register
  - Current-State Workflow Sketch
  - Fact, Derivation, Assumption and Question Register
  - Investigation Hypotheses
  - Input Sufficiency and Framing Mode
  - Evidence Acquisition Backlog
  - Early Waste Signals
  - Lean / DMAIC Lens
---
# Prompt 01 — Discovery (AI FDE Inputs)

Establish the factual foundation for every later stage of this pipeline: **business context,
user workflow, constraints, evidence, and stakeholder needs.** Do not propose a target
architecture, a tool selection, or a risk model here — that is later work, and it must be built on
what this stage actually found, not on what this stage assumed.

When the use case and evidence are thin, still produce every section below — but score
sufficiency honestly, produce an evidence acquisition backlog, and declare whether the next stage
may treat this as `decision-ready` or must proceed as `hypothesis`. A thin evidence base is not a
reason to invent; it is a reason to say so.

## Repository and Evidence Map

What exists, where it lives, and how it connects: the repository and source-system map; entities,
identifiers, and timestamp semantics (what is tracked, how it is named, what time means in each
context — event time vs. report time, where observable); evidence ownership and authority (source
of truth for each material data class, and who or what may assert it); and material
inconsistencies, gaps, and conflicts — where the evidence disagrees, is missing, or cannot be
trusted. Also capture stakeholder decisions and decision horizons: what is already decided, what
is pending, and by when.

## Constraints Register

Technical, risk, compliance, security, privacy, and operational constraints already visible in the
use case and evidence — not constraints you infer should exist, only ones you can point to.

## Current-State Workflow Sketch

How the work is done today, as observed — not redesigned, not improved. Mark any inferred step
explicitly as an assumption.

## Fact, Derivation, Assumption and Question Register

Classify every material finding into exactly one of: **fact** (directly stated in the use case or
evidence), **derivation** (follows necessarily from facts), **assumption** (plausible but
unverified — must be labeled as such), or **open question**. A table with a stable ID per row.

## Investigation Hypotheses

The ten most important hypotheses for later stages to test, ranked by how much they would change
framing or design if confirmed or refuted.

## Input Sufficiency and Framing Mode

Rate each AI FDE input **Strong / Partial / Missing**, with what exists and what is missing for
each: business context, user workflow, constraints, evidence (data, logs, research), stakeholder
needs.

Then declare the **framing mode** for the next stage — this is required, not optional:

- `decision-ready` — the Situation and Complication can be written mainly from facts and
  derivations, with no critical fact invented.
- `hypothesis` — one or more inputs are Partial or Missing to the point that framing must proceed
  as a testable hypothesis, not a locked decision.

Rule of thumb: if **evidence** or **user workflow** is Missing, or two or more inputs are Missing,
default to `hypothesis` unless you can justify overriding it.

## Evidence Acquisition Backlog

An ordered list of what to obtain next. For each item: the artifact needed, its likely owner or
source, which later stage it blocks, and priority (blocks framing / blocks design / blocks
production). If every input above is Strong, state that explicitly rather than omitting the
section.

## Early Waste Signals

While inspecting the current workflow, note observed or hypothesized waste using the DOWNTIME
letters and AI-specific waste names where visible (e.g. Waiting on approvals, Extra processing,
Token or Retrieval waste) — mark each **observed** vs **hypothesized** per house style. This is a
preview, not a workshop: do not attempt the full waste registers here; that belongs to the
dedicated Lean/DMAIC consolidation stage later in the pipeline.

## Lean / DMAIC Lens

This stage's focus is **Measure** (baseline signals) and light **Define** (what improvement space
exists). Record: what can already be measured today (cycle time, error rate, backlog, token or
cost signals, review lag); which baselines are `Unknown`; the top three early waste signals with
observed vs. hypothesized; and what must be measured before any automation here is scaled.

Use exactly these `##` section headings, in this order: Repository and Evidence Map, Constraints
Register, Current-State Workflow Sketch, Fact, Derivation, Assumption and Question Register,
Investigation Hypotheses, Input Sufficiency and Framing Mode, Evidence Acquisition Backlog, Early
Waste Signals, Lean / DMAIC Lens.
