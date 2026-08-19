---
id: stage.decisions
version: 2.0.0
stage: decisions
model_role: generator
inputs: [use_case, evidence, prior_artifacts]
output_format: markdown
required_sections:
  - Decision Records
  - Decision Index
  - Architecture Review
  - Lean / DMAIC Lens
---
# Prompt 07 — Architecture Decision Records and Review

For each significant choice visible on the C4 map or the security model, record the decision
memory behind it: context, decision, consequences, status, alternatives, guardrails, validation,
and a revisit trigger. Together, architecture and decision records are **structure and
rationale** — C4 says what the system looks like, this stage says why.

If the architecture or domain model is `provisional`, or the narrative class carried from SCQA is
`hypothesis`, keep material decisions at status `proposed` until validation evidence exists — do
not mark one `accepted` without evidence, or without an explicit interim assumption plus a revisit
trigger.

## Decision Records

Produce **at least five** decision records, drawn from the architecture stage's and the security
stage's decision candidates — prefer decisions that affect identity, evidence, authority, AI
behaviour, or operability. Suggested themes, use what applies: entity identity across systems;
event time vs. report time; canonical models and source translation; rules vs. AI vs.
explainability; data persistence and evidence snapshots; online, intermittent, and offline
operation; role and authority enforcement including HITL; decision audit; retrieval and model-use
boundaries; agent tool permissions and stop conditions; external integrations; deployment and
observability.

One subsection per decision (`### ADR-001 — <title>`, sequential), each with every field below —
omitting a field is not a shorter ADR, it is an incomplete one:

- **Status** — `proposed` | `accepted` | `deprecated` | `superseded by ADR-<N>`, with a date.
- **Owner** — the accountable role, drawn from the use case's stakeholders.
- **Related elements** — the C4 element(s), bounded context(s), and feature ID(s) this decision
  touches.
- **Evidence basis** — `fact` | `derivation` | `assumption`, tied back to Discovery.
- **Context** — the forces at play, cited to the use case or evidence by name.
- **Decision drivers** — the primary influencing factors, including relevant non-functional
  requirements.
- **Options considered** — at least two real alternatives, each with its trade-off; not a
  strawman.
- **Decision** — the option chosen, stated plainly.
- **Rationale** — why this option over the others, tied to the drivers.
- **Consequences** — positive, negative, and risks introduced.
- **Security and privacy impact** — threats addressed, data classes touched, controls applied
  (consistent with the security-model stage).
- **Operational impact** — deploy and rollback story, monitoring signal, alert condition.
- **Guardrails** — the domain invariants or policies this decision must never violate, and an
  explicit statement that any prohibited operational write path remains absent by construction.
- **Validation** — how this decision will be tested or verified.
- **Revisit trigger** — quantified where possible (e.g. "when p95 ingestion lag exceeds N
  minutes"); **required** whenever status is `proposed` or the evidence basis is `assumption`.

## Decision Index

A table linking every decision record to the C4 elements and bounded contexts it touches, and
listing which decisions are blocked on an item in Discovery's evidence acquisition backlog.

## Architecture Review

After the decisions above are recorded, defend the map before it hardens into contracts. State a
**review status**: `pass` | `conditional` | `fail`. Check: the C4 map matches the domain model's
bounded contexts and the in-scope features; every material trade-off has a decision record; trust,
authority, privacy, degraded-mode behaviour, and prohibited writes are all visible on the map;
Gen AI, HITL, and rules boundaries are placed; nothing the PRD marked out-of-scope has been
smuggled into a container. List open issues as blockers vs. accepted residual risk. State the
go-forward decision: proceed only if `pass`, or `conditional` with named conditions; a `fail`
means returning to the architecture or security-model stage before continuing. Under `provisional`
or `hypothesis`, prefer `conditional` unless the evidence genuinely supports `pass`.

## Lean / DMAIC Lens

This stage's focus is **Analyze** (trade-offs that create or remove waste) and setting **Control**
revisit triggers. Record: which decisions explicitly prevent a named waste (e.g. rules-before-AI
preventing Defect or Model waste); which decisions risk introducing new Waiting, human-review, or
token waste; which validation and revisit triggers will serve Control later in this pipeline; and
whether any architecture-review open issue is really a waste risk in disguise.

Do not silently change the domain model — if a decision requires one, note it as a domain-model
revision instead. Do not write full API schemas here; that is the technical-design stage. Do not
mark an assumption-based decision `accepted` without its interim-assumption and revisit-trigger
fields filled. Do not skip the architecture review. Prefer fewer, sharp decision records over many
vague ones.

Use exactly these `##` section headings, in this order: Decision Records, Decision Index,
Architecture Review, Lean / DMAIC Lens.
