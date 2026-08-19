---
id: stage.feature_specs
version: 1.0.0
stage: feature_specs
model_role: generator
inputs: [use_case, evidence, prior_artifacts]
output_format: markdown
required_sections:
  - Feature Index
  - Feature Specifications
  - Business Rules and Acceptance Criteria Registers
  - Ambiguities
  - Lean / DMAIC Lens
---
# Prompt 05 — Feature Specifications

Derive feature specifications from the PRD's in-scope capabilities and the domain model's
ubiquitous language: workflows, business rules, edge cases, and acceptance criteria — one feature,
clearly delimited, per entry. Use the domain's own vocabulary; do not invent technical contracts
here (APIs and schemas belong to the technical-design stage). Keep unrelated features cleanly
separated within this document the way separate files would keep them separated — a reader must be
able to review one feature without wading through another.

## Feature Index

Every in-scope-for-this-version feature, each with: an ID (`FR-001`, sequential), a name, the
bounded context that owns it, a priority, and a status (`stable` | `provisional`, inherited from
the domain model unless this specific feature has its own open question).

## Feature Specifications

One subsection per feature (`### FR-001 — <name>`, one heading per feature, in ID order), each
containing: the actor(s); preconditions — what must already be true; the happy-path flow as
ordered steps in business language; exceptions and alternate paths; numbered, testable business
rules (`BR-00N`) tied to this feature; binary, testable acceptance criteria (`AC-00N`) that need no
meeting to adjudicate; the HITL/AI boundary where this feature involves AI — what it may do versus
what stays a rule or a human decision, consistent with the domain model's boundaries; what this
feature deliberately excludes; and any ambiguity — an unspecified threshold, a missing value, an
undefined rejection behaviour — that must not be left silent.

If a feature involves matching, classification, detection acceptance, or any confidence-gated
decision, also specify within its subsection: the priority order of match strategies (fixed order,
not "best effort"); the numeric acceptance threshold per stage, or an explicit `Unknown` logged to
the ambiguities section; the rejection behaviour below threshold, in business language; and any
deduplication or quantity rule if repeated detections are possible. Do not leave "validate
confidence" or "fuzzy match" without either a number or an explicit `Unknown`.

## Business Rules and Acceptance Criteria Registers

Two consolidated tables, each row referencing its owning feature ID: every `BR-00N` across all
features, and every `AC-00N` across all features. This is what a technical-design or task-planning
stage reads to build a traceability matrix — keep the IDs stable once assigned.

This section is **mandatory and separate** from the per-feature detail above — listing `BR-00N`s
and `AC-00N`s inside individual `### FR-00N` subsections does not satisfy it. Produce this section,
under its own `##` heading, with both tables, even when there is only one feature.

## Ambiguities

Every threshold, error behaviour, or state rule left open across all features, consolidated in one
place rather than buried inside individual feature subsections — each with which feature it
belongs to and what would resolve it.

## Lean / DMAIC Lens

This stage's focus is **Analyze** (failure and rework paths) and **Improve** by specifying flows
that are less wasteful by design. Record, per critical feature: which acceptance criterion or
business rule prevents a Defect or Extra-processing waste; where an exception path creates Waiting
or Inventory waste (a queue, an unreviewed output); which confidence or matching ambiguity would
cause retries, false accepts, or review waste if left unresolved; and any feature that looks like
Overproduction relative to what the PRD actually scoped.

Every in-scope PRD capability must map to at least one feature here, or an explicit, named
deferral — do not silently drop one. Do not pull a PRD out-of-scope item back in without updating
the PRD stage first. Do not produce a C4 diagram or an endpoint table here — that is later work.

Use exactly these `##` section headings, in this order: Feature Index, Feature Specifications,
Business Rules and Acceptance Criteria Registers, Ambiguities, Lean / DMAIC Lens. Before finishing,
re-check that all five appear verbatim — Business Rules and Acceptance Criteria Registers is the one
most often dropped, because its content overlaps with the per-feature detail above; produce it as
its own section regardless.
