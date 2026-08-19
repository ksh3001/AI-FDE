---
id: stage.security_model
version: 1.0.0
stage: security_model
model_role: generator
inputs: [use_case, evidence, prior_artifacts]
output_format: markdown
required_sections:
  - Zone Architecture
  - Threat Model
  - Retrieval Entitlement Boundary
  - Tool Permission Matrix
  - Human Approval Matrix
  - Evidence and Audit
  - Security Decision Candidates
  - Lean / DMAIC Lens
---
# Prompt 06A — Security and Threat Model

Turn the C4 map into a defensible trust architecture. The architecture stage said what the
containers are; this stage says where the boundaries sit, what is allowed to cross them, and what
is refused. Guardrails are layered, not a single feature — relevance classification, safety
filtering, PII protection, moderation, tool-risk assessment, and human review for high-risk
actions. In regulated work these **are** the architecture, not an add-on bolted onto it.

The decisions made here become decision-record candidates, implemented as contracts in the
technical-design stage. Record them as decisions with alternatives, not as assertions. If the
architecture's artifact status is `provisional`, this model is provisional too — but an
enforcement point is never optional just because the map around it is still settling. A
provisional map with no access-control boundary is not provisional, it is unsafe.

## Zone Architecture

Place every container from the architecture stage into exactly one zone: user access (portal, API
edge); security control (gateway, DLP, prompt-injection checks); data access (retrieval services,
tool gateway); model serving (router, inference runtime); sandbox (isolated execution, no
production credentials); governance (registries, evaluation, audit); observability (logs, metrics,
traces, alerts — no prompt or PII content in the attributes themselves). A container in no zone is
an unowned attack surface. State the environment promotion path (e.g. development → integration →
staging → production) and what may not be promoted without a gate.

There must be no direct user-to-model path: every request enters through the security-control zone
and leaves through validation. If the architecture stage's map shows a bypass, raise it back as a
defect there — do not quietly design around it here.

## Threat Model

For each threat: entry point, affected zone, existing control, residual risk, and `observed` vs
`hypothesized` per house style. Cover four layers. **Model** — direct and indirect prompt
injection (including via retrieved content), jailbreak or instruction override, system-prompt
extraction, unsafe or defamatory generation. **Data** — retrieval of unentitled documents,
cross-tenant cache bleed, PII egress in prompts/logs/telemetry, residency violation, stale content
presented as current. **Action** — tool invocation beyond authority, a non-idempotent write
replayed, generated code or a query executed outside the sandbox, an unauthorised write to a
system of record, an agent loop exhausting its budget. **Supply and operations** — an unpinned
model or prompt version changing behaviour silently, a dependency or plugin compromise, a secret
exposed in a prompt or log, a material decision with no audit record.

For each threat, give it exactly one disposition: prevented by design; detected and blocked;
detected and alerted; or accepted residual risk with a named owner and trigger. "Mitigated" with
none of these four named is not an answer.

## Retrieval Entitlement Boundary

State and justify the enforcement point: pre-retrieval ACL filtering (scope retrieval to entitled
sources before anything enters model context — prefer this), retrieve-everything-then-filter, or
retrieve-everything-then-redact. The latter two allow unauthorised data to influence generation
even when never displayed; if either is chosen, record the alternatives you rejected and why.
Specify temporal or effective-date filtering where policy versions matter, source-of-truth
precedence when sources conflict, and what happens when entitlement is unknown — deny by default,
with any exception named explicitly.

## Tool Permission Matrix

One row per tool: read or write; risk tier; policy (allowed freely / allowed with approval /
dry-run only / denied); idempotency; approval requirement. Separate read from write. Key the
matrix on access context, not job title. Name deny cases explicitly rather than leaving them as
absence. Define what the circuit breaker does when a tool misbehaves or a budget is exceeded. The
model may request a tool; state plainly that the platform decides whether it runs.

## Human Approval Matrix

Drive triggers from risk attributes, not from a job title: customer-impacting, financially
impacting, a regulated decision, external communication — each with an approver role, what the
approver must see (evidence, rule trace, tool outputs), and an escalation path. Record attestation
outcomes as approve / edit / reject / escalate, all logged. Challenge over-approval as hard as
under-approval: if every path needs review, the system adds no value, and human-review waste is
the result — name which flows are deliberately exempt and why.

## Evidence and Audit

What lands in the audit store on every request, including failures and refusals. The version
identifiers that travel with every answer — model, prompt template, embedding model, index, rule
set. Retention period and who may read the audit store. The test to hold this section to: could an
auditor reconstruct why this answer was given, from the stored objects alone?

## Security Decision Candidates

List the choices above that need a decision record — entitlement enforcement point, tool-gateway
posture, sandbox boundary, approval triggers, version pinning, key and identity model. Options
visible; decisions recorded in the next stage.

## Lean / DMAIC Lens

This stage's focus is **Improve** (controls that remove Defect and rework waste) and **Control**
(enforcement points that hold). Record: which controls prevent a Defect (unentitled retrieval, an
injected instruction, an unsafe write) rather than merely detecting it afterward; where the
approval matrix risks human-review waste, and which low-risk flows are deliberately kept out of
the queue; whether logging and evidence requirements risk observability waste (records with no
owner and no decision they inform); and which security checks are duplicated across zones (extra
processing) versus enforced once at a single boundary.

Do not redraw the C4 map here — if security requires a structural change, raise it back to the
architecture stage and flag a decision record. Do not write API schemas, headers, or error codes;
that is the technical-design stage. Do not map compliance controls or build a Statement of
Applicability here; that is the compliance stage that follows. Do not list a threat without a
disposition, and do not accept a residual risk without a named owner and trigger.

Use exactly these `##` section headings, in this order: Zone Architecture, Threat Model, Retrieval
Entitlement Boundary, Tool Permission Matrix, Human Approval Matrix, Evidence and Audit, Security
Decision Candidates, Lean / DMAIC Lens.
