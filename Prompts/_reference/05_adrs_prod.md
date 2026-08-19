# Prompt 05 (Production) — Production-Ready ADRs

> Production-grade variant of `05_adrs.md`. Use this when the architectural decisions
> must stand up to a **real deployment** — live data, real users, uptime, security and operations —
> not only the demonstrable prototype. Run it after the C4 views (`participant-outputs/04-c4/`) and
> the DDD model (`participant-outputs/03-ddd/`) exist. Attach: the SCQA narrative, the domain
> landscape (invariants `INV-*` / policies `POL-*`), the C4 views, `{AUTHORITY_MATRIX}`,
> `{SOURCE_SYSTEMS}`, and `case-study/03_constraints_authority_and_non_negotiables.md`.

You are the architecture assistant producing **Architectural Decision Records for a production
deployment** of the `{SYSTEM}` advisory decision-support system.

## Mission

Create **at least eight** ADRs that make **production-ready** architectural decisions. Every ADR
must be justified for a system that runs continuously, ingests **live/changing** data, serves
authenticated users across all locations of use (including intermittently connected ones), and is
operated, secured, monitored and evolved over time — while remaining strictly **advisory**.

## Non-negotiable constraints (carry at any scale — never relaxed for production)

1. **Advisory only.** No operational write-back; no control of operational/machinery/transactional
   systems; no declaration of fitness, compliance or acceptance; no execution of commercial
   transactions (`{PROHIBITED_ACTIONS}`). Production makes these *more* strictly enforced, never less.
2. **Human authority always identifiable** for every decision, drawn from `{AUTHORITY_MATRIX}`.
3. **Evidence discipline is first-class.** Preserve source vs receipt vs report time + timezone;
   preserve original identifiers; keep conflicts visible; never treat missing data as normal; expose
   formula/source/units for derived values; resolve identity without destroying provenance.
4. **`{PRIORITY_RULE}`** may never be overridden (e.g. safety/environmental/security/compliance/
   statutory authority is never overruled by commercial urgency).

## Decision areas to cover (choose ≥8; combine sensibly)

Business/domain decisions (as in the base prompt):
- entity, process and event identity resolution;
- source-event time vs report vs receipt time;
- canonical model and per-source translation (ACL);
- rules, analytics and explainability;
- data persistence and evidence snapshots;
- online, intermittent and offline operation;
- role and authority enforcement;
- decision audit and non-repudiation.

**Production/operational decisions (this variant additionally requires):**
- **Deployment topology & runtime** — monolith vs services vs modular deployable units; containers/
  orchestration; environments (dev/stage/prod); infrastructure-as-code.
- **Live ingestion & integration** — connectors to real source systems; delivery semantics
  (at-least-once/exactly-once), idempotency, back-pressure, schema evolution/versioning, replay/
  backfill; **read-only toward all source/operational systems**.
- **Scalability & performance** — throughput and latency budgets/SLOs for ingestion, prioritization
  and query; capacity and horizontal-scaling strategy; caching.
- **Availability, resilience & DR** — uptime target/SLA, failure isolation, retries/circuit breakers,
  backup/restore, RPO/RTO, multi-AZ/region posture, graceful degradation.
- **Security & threat model** — authN/authZ (SSO/OIDC), secrets management, network/trust zones,
  encryption in transit and at rest, tenancy/isolation, supply-chain integrity, and an explicit
  threat model for the remote-access/integration surface.
- **Data protection & privacy** — classification (restricted vs operational vs reference),
  data minimization, retention/purge, access logging, and residency.
- **Observability & operations** — logging/metrics/tracing, SLOs & alerting, audit/lineage,
  runbooks, on-call, and how *determinism* and *provenance* are proven in production.
- **Release & change management** — CI/CD, testing gates, migrations, feature flags, rollback/
  roll-forward, and how a rule/weight change is reviewed and audited.
- **Cost & sustainability** — cost drivers and controls; footprint of high-volume telemetry.

## Required content per ADR

Use `templates/10_adr_template.md` and, for this production variant, **extend** each ADR with:

- **Status / Date / Owners**, and **Related requirements / bounded contexts / C4 elements**.
- **Context** and **Decision drivers** (include the relevant NFRs).
- **Options considered** — ≥3 realistic alternatives, each with the trade-off stated.
- **Decision** and **Rationale**.
- **Non-functional targets (SLO/NFR)** — concrete, measurable (e.g. p95 latency, availability %,
  RPO/RTO, ingestion lag, max data-staleness surfaced to users).
- **Security & privacy impact** — threats addressed, data classes touched, controls applied.
- **Operational impact** — deploy/rollback story, monitoring signals, alert conditions, runbook note.
- **Consequences** — positive / negative / **risks introduced**.
- **Guardrails** — tied to `INV-*` / `POL-*` and the non-negotiables above; assert the prohibited
  operational write paths are absent by construction.
- **Validation** — tests **and** production checks (load/chaos/failover/security test, SLO monitor,
  architecture/dependency check proving no source-write path).
- **Revisit trigger** — quantified where possible (e.g. "when ingestion lag p95 > N min" or
  "when a new source family is onboarded").

## Quality gate (self-check before finishing)

- ≥8 ADRs; every listed production decision area is covered by at least one ADR.
- Every ADR states measurable NFRs/SLOs and a security/privacy and operational impact.
- No decision weakens the advisory boundary, authority visibility, evidence discipline, or the
  `{PRIORITY_RULE}` — at production scale these are strengthened.
- Every prohibited operational write path remains absent by construction and is asserted by a test.
- Each ADR names alternatives, guardrails (traced to `INV-*`/`POL-*`), validation (incl. a
  production check), and a quantified revisit trigger.
- ADRs are internally consistent with the C4 views and each other; where a production choice differs
  from the prototype, note the migration path.

Write outputs to `participant-outputs/05-adrs/prod/` (production ADRs; prefix filenames or add a
`Status`/scope note so they are distinguishable from any prototype-scoped ADRs).
