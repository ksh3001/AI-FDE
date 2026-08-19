# ADR-{NUMBER} — {TITLE}

> Referenced by `prompts/05_adrs.md` and `prompts/05_adrs_prod.md`. Fields marked
> **(prod)** are required only when the production ADR variant is in use; the
> prototype variant may omit them.

## Status

{Proposed | Accepted | Superseded by ADR-{N} | Deprecated} — {DATE}

## Owners **(prod)**

{accountable role(s), drawn from `{AUTHORITY_MATRIX}`}

## Related requirements / bounded contexts / C4 elements

- Requirement(s): {...}
- Bounded context(s): {...}
- C4 element(s): {...}

## Context

{The forces at play — technical, business, evidence, or authority constraints
that make this decision necessary. Cite the use case / evidence by filename.}

## Decision drivers

- {driver 1, including relevant NFRs}
- {driver 2}

## Options considered

1. **{Option A}** — {trade-off}
2. **{Option B}** — {trade-off}
3. **{Option C}** — {trade-off}

*(≥3 realistic alternatives required for the prod variant; ≥1 alternative for the
prototype variant.)*

## Decision

{The option chosen, stated plainly.}

## Rationale

{Why this option over the others, tied back to the decision drivers.}

## Non-functional targets (SLO/NFR) **(prod)**

{Concrete, measurable — e.g. p95 latency, availability %, RPO/RTO, ingestion lag,
max data-staleness surfaced to users.}

## Security & privacy impact **(prod)**

{Threats addressed, data classes touched, controls applied.}

## Operational impact **(prod)**

{Deploy/rollback story, monitoring signals, alert conditions, runbook note.}

## Consequences

- **Positive:** {...}
- **Negative:** {...}
- **Risks introduced:** {...}

## Guardrails

{Tied to `INV-*` / `POL-*` domain invariants and policies, and to the
non-negotiables — advisory-only, human authority visible, evidence discipline,
`{PRIORITY_RULE}`. Assert that any prohibited operational write path is absent
by construction.}

## Validation

{Tests — and, for the prod variant, production checks: load/chaos/failover/
security test, SLO monitor, architecture/dependency check proving no
source-write path.}

## Revisit trigger

{Quantified where possible — e.g. "when ingestion lag p95 > N min" or "when a
new source family is onboarded".}
