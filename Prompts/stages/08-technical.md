---
id: stage.technical_design
version: 1.0.0
stage: technical_design
model_role: generator
inputs: [use_case, evidence, prior_artifacts]
output_format: markdown
required_sections:
  - API and Interface Contracts
  - Data Model
  - State Transitions
  - Non-Functional Requirements
  - Error Envelope and Security Controls
  - Module and Layering Rules
  - Traceability Matrix and Gap Audit
  - Ambiguity Closure
  - Deployment Notes
  - Lean / DMAIC Lens
---
# Prompt 08 — Technical Design

This is the layer that pays for anything built from this pack: exact request and response shapes,
validation with real values, error paths with status codes, state transitions, the data model, and
measurable non-functional requirements. The architecture stage said *where* code belongs; the
decision records said *why*; this stage says *exactly how it behaves*, so nothing material is left
to guess at build time.

## API and Interface Contracts

For each endpoint or interface the in-scope features need: method and path (or message name);
request schema with validation rules stated as real values, never adjectives; response schema for
success; error cases with status codes; and idempotency and auth expectations if in scope — or, if
authentication is explicitly out of scope, say so and what that implies for deployment.

## Data Model

Entities, tables, or collections with fields and types; identity and timestamp semantics;
relationships and constraints; and what must never be written back, consistent with the
architecture and security-model stages.

## State Transitions

Session or entity state machines where they apply, with their triggers and illegal transitions
named.

## Non-Functional Requirements

Measurable only: latency budgets, coverage targets, logging, transactionality, deployment
constraints. An untestable preference is not an NFR — if you cannot write a check for it, it does
not belong here.

## Error Envelope and Security Controls

A standard error response shape; validation, injection safety, CORS, logging and correlation IDs,
and a statement that internal traces never reach a client response.

## Module and Layering Rules

Folder or module layout aligned to the C4 containers, stated as enforceable constraints an agent
can be held to — e.g. routers hold no business logic, services hold no raw queries, the UI never
bypasses the API.

## Traceability Matrix and Gap Audit

A table: feature/FR → endpoint(s) or contract → business rules → acceptance criteria → decision
record(s) → ambiguity status (`resolved` / `assumed` / `open`). Then audit it for orphans and name
every one found, do not leave any unmarked: a feature with no acceptance criterion; a business rule
with no verifying criterion, or no numeric threshold where it needs one; an acceptance criterion
with no endpoint or contract; an endpoint with no feature behind it; a matching or confidence rule
with no number (or an explicit `Unknown` with a backlog link); an error-envelope or security rule
with no acceptance criterion or NFR check. Every gap found here must be fixed now, assumed with a
revisit trigger, or explicitly open-blocked.

## Ambiguity Closure

Resolve every item in the feature-specs stage's ambiguities register with a real value, or mark it
**assumed** with a revisit trigger, or **open** — which blocks any related work downstream. For
matching or classification features, lock the priority order and the numeric thresholds, or
document the specific blocker preventing that.

## Deployment Notes

Lightweight only: containerisation, environment configuration, health checks, reverse-proxy
expectations — stated as measurable NFRs, or explicitly marked out of scope.

## Lean / DMAIC Lens

This stage's focus is **Improve** — contracts that prevent token, retrieval, integration, and
evaluation waste — and setting measurable NFRs for later **Measure** and **Control**. Record:
which contract choices cap token, retrieval, or context waste (limits, filters, pagination); which
error and retry rules avoid blind Model waste (a retry with no diagnosis of the cause); which NFRs
are actually measurable Control metrics rather than aspirational targets; and which ambiguities
left open here would cause extra processing once someone tries to build against this pack.

Do not describe implementation steps or write actual code here — that is outside this pipeline's
scope. Do not expand the PRD's out-of-scope boundary. Do not leave an open ambiguity unmarked for
anything the traceability matrix shows as in-scope.

Use exactly these `##` section headings, in this order: API and Interface Contracts, Data Model,
State Transitions, Non-Functional Requirements, Error Envelope and Security Controls, Module and
Layering Rules, Traceability Matrix and Gap Audit, Ambiguity Closure, Deployment Notes, Lean /
DMAIC Lens.
