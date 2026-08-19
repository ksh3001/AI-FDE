# Prompt 06A — Security & Threat Model (Design — Trust Boundaries)

**Lifecycle stage:** Design (system) — security view of the C4 map  
**Framework derived:** Layered GenAI security zones + governed tool/retrieval boundaries; Azure Well-Architected (Security pillar) for AI workloads  
**Core question:** What data reaches the model, who may see the output, and what stops the rest?  
**Prerequisites:** Prompt 02A risk tier and architecture consequences; Prompt 04 Gen AI boundaries (rules vs AI vs HITL); Prompt 06 C4 views.  
**Primary output type:** Zone architecture, threat model, and enforcement matrices (may be provisional).

---

## Intent

Turn the C4 map into a **defensible trust architecture**. Prompt 06 said what the containers are; this prompt says where the boundaries sit, what crosses them, and what is refused.

Guardrails are **layered, not a feature**: relevance classification, safety filtering, PII protection, moderation, tool-risk assessment, and human-in-the-loop for high-risk actions. In regulated work these *are* the architecture — not an add-on bolted to it.

The decisions made here become ADRs in Prompt 07 and are implemented as contracts in Prompt 08. Record them as decisions with alternatives, not as assertions.

If Prompt 06 artifact status is `provisional`, this model is provisional too — but **enforcement points may not be deferred**. A provisional map with no ACL boundary is not provisional, it is unsafe.

---

## Entry criteria

- C4 Context / Container / Component views exist.
- Prompt 02A risk tier, permitted autonomy, and logging floor are known.
- Rules vs AI vs HITL boundaries from Prompt 04 are available.
- Prohibited operational write paths (Prompt 06) are listed.
- Data classification and residency constraints from Prompt 01 are available or marked Unknown.

---

## Produce

**Artifact status (required):** `stable` | `provisional` (inherit from Prompt 06 unless evidence justifies otherwise).

### A. Zone architecture

Place every container from Prompt 06 into exactly one zone. A container in no zone is an unowned attack surface.

| Zone | Contains | Enforces |
|---|---|---|
| User access | Portal, API edge | Authentication, session, rate limiting |
| Security control | Gateway, DLP, prompt-injection checks | Everything crossing into the system |
| Data access | Retrieval services, tool gateway | Entitlement before data leaves the store |
| Model serving | Model router, inference runtime | Tenant isolation, model/version pinning |
| Sandbox | Isolated code / file / query execution | No egress; no production credentials |
| Governance | Registries, evaluation, audit, evidence | Immutability, retention |
| Observability | Logs, metrics, traces, alerts | No prompt/PII content in attributes |

Also state the **environment promotion path** (development → integration → staging → production → regulated production, or the project's equivalent) and what may not be promoted without a gate.

**Structural rule:** no direct user-to-model path. Every request enters through the security control zone and leaves through validation. If the C4 map shows a bypass, raise it as a Prompt 06 defect, do not document around it.

### B. Threat model

For each threat, record: entry point, affected zone, existing control, residual risk, and `observed | hypothesized`.

**Model-layer:** direct prompt injection · indirect injection via retrieved content · jailbreak / instruction override · system-prompt extraction · training or few-shot data leakage · unsafe or defamatory generation.

**Data-layer:** retrieval of unentitled documents · cross-tenant cache bleed · PII egress in prompts, logs, or telemetry · residency violation via model or storage region · stale or superseded source presented as current.

**Action-layer:** tool invocation beyond authority · non-idempotent write replayed · generated code or query executed outside sandbox · unauthorised write to a system of record · agent loop exhausting budget or rate limits.

**Supply and operations:** unpinned model or prompt version changing behaviour silently · dependency or plugin compromise · secret in prompt, repository, or log · missing audit record for a material decision.

For each: **prevented by design · detected and blocked · detected and alerted · accepted residual risk (owner + trigger)**. "Mitigated" without one of these four is not an answer.

### C. Retrieval entitlement boundary

State and justify the enforcement point:

1. **Pre-retrieval ACL filtering** — scope retrieval to entitled sources before any document enters model context.
2. Retrieve everything, filter the final answer.
3. Retrieve everything, redact the output.

Options 2 and 3 allow unauthorized data to influence generation even when it is not displayed. Prefer option 1 and record the alternatives as rejected, with the metadata and entitlement-mapping synchronisation this obliges — and the rollback position if entitlement cannot be verified for a corpus.

Also specify: temporal / effective-date filtering where policy versions matter, source-of-truth precedence when sources conflict, and what the system does when entitlement is **unknown** (deny is the default; document any exception).

### D. Tool permission matrix

| Tool | Read / Write | Risk tier | Policy | Idempotency | Approval |
|---|---|---|---|---|---|
| | | | freely / with approval / dry-run only / denied | | |

Rules: read and write are separated; every write tool declares idempotency and an approval requirement; the matrix keys on **access context, not job title**; deny cases are named explicitly rather than left as absence. Define circuit-breaker behaviour when a tool misbehaves or a budget is exceeded.

**The model may request a tool; the platform decides whether it runs.** State where that decision is enforced.

### E. Human approval matrix

Drive triggers from risk attributes, not from a job title:

| Trigger attribute | Approver role | Must see | Escalation path |
|---|---|---|---|
| customer-impacting | | evidence, rule trace, tool outputs | |
| financially impacting | | | |
| regulated decision | | | |
| external communication | | | |

Record attestation outcomes as `approve | edit | reject | escalate`, all logged.

**Challenge over-approval as hard as under-approval.** If every path needs review, the system adds no value and creates human-review waste. Risk tiering exists so low-risk flows run without a queue — say which flows those are.

### F. Evidence, reproducibility and audit

- What lands in the audit store on **every** request — including failures and refusals.
- Version identifiers that travel with each answer: model, prompt template, embedding model, index, rule set.
- Retention period and who may read the audit store.
- The test: *could an auditor reconstruct why this answer was given, from the stored objects alone?*

### G. Security decision candidates (for Prompt 07)

List the choices above that require ADRs — entitlement enforcement point, tool gateway posture, sandbox boundary, approval triggers, version pinning, key and identity model. Options visible; decisions recorded in Prompt 07.

### Lean / DMAIC lens (spine — thin)

**DMAIC focus this stage:** **Improve** (controls that remove Defect and rework waste) + **Control** (enforcement points that hold).

In `dmaic_lens.md` (short), record:

1. Which controls prevent **Defects** (unentitled retrieval, injected instructions, unsafe writes) rather than detecting them after the fact?
2. Where does the approval matrix risk **Human-review waste** — which low-risk flows are deliberately kept out of the queue?
3. Do logging and evidence requirements create **Observability waste** (records with no owner and no decision they inform)?
4. Which security checks are duplicated across zones (**Extra processing**) versus enforced once at a single boundary?

---

## Exit criteria (handoff to Prompt 07)

- [ ] Artifact status (`stable` | `provisional`) is stated.
- [ ] Every Prompt 06 container is placed in exactly one zone; no direct user-to-model path exists.
- [ ] Threat model covers model, data, action, and supply/operations layers, each with a disposition of the four permitted kinds.
- [ ] Retrieval entitlement enforcement point is chosen, with alternatives recorded as rejected.
- [ ] Tool permission matrix separates read from write and names deny cases and circuit-breaker behaviour.
- [ ] Human approval matrix keys on risk attributes, names what the reviewer sees, and identifies flows deliberately exempt.
- [ ] Evidence package satisfies the auditor-reconstruction test; version identifiers travel with answers.
- [ ] Security decision candidates are listed for ADR capture in Prompt 07.
- [ ] Residual risks each carry an owner and a revisit trigger.
- [ ] `dmaic_lens.md` is complete (feeds Prompt 09).

---

## Constraints

- Do not redraw the C4 map here; if security requires a structural change, raise a Prompt 06 revision and flag an ADR.
- Do not write API schemas, headers, or error codes — that is Prompt 08.
- Do not map ISO 42001 Annex A controls or build the Statement of Applicability — that is Prompt 07A.
- Do not list a threat without a disposition; "monitored" is not a control unless an alert has an owner and a threshold.
- Do not accept a residual risk without an owner and a trigger.
- Do not exceed the autonomy permitted by the Prompt 02A tier, even where technically straightforward.
- Do not run full Prompt 09 here.

---

## Output

Write under `participant-outputs-v2/06A-security/` **and mirror** to `specs/architecture/`:

- `zone_architecture.md`
- `threat_model.md`
- `retrieval_entitlement.md`
- `tool_permission_matrix.md`
- `human_approval_matrix.md`
- `evidence_and_audit.md`
- `security_decision_candidates.md`
- `dmaic_lens.md`
