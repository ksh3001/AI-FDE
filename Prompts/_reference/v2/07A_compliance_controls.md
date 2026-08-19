# Prompt 07A — Compliance Controls & Statement of Applicability (Govern)

**Lifecycle stage:** Decide → Govern (control design before technical contracts)  
**Framework derived:** ISO/IEC 42001:2023 (Annex A controls, Statement of Applicability, AI system impact assessment) + EU AI Act Art. 8–15 high-risk requirements  
**Core question:** Which controls apply, where is each one implemented, and what evidence proves it?  
**Prerequisites:** Prompt 02A classification and obligation register; Prompt 06A threat model and enforcement matrices; Prompt 07 ADRs and architecture review.  
**Primary output type:** Statement of Applicability, control-to-implementation map, and AI system impact assessment.

---

## Intent

Convert obligations into **named controls with named implementations and named evidence**. Prompt 02A said which duties attach; Prompt 06A designed the technical enforcement; this prompt closes the loop — every obligation maps to a control, every control maps to where it lives, and every control names the artefact that would prove it to an auditor.

The failure mode this prevents is **checklist theatre**: passing every framework question on paper while the real risk — no ground truth, no named owner, no evidence trail — is not on the checklist. A control with no implementation and no evidence is a claim, not a control.

Design-time only. Whether controls actually *work* in the built system is Prompt 12.

If artifacts upstream are `provisional` or the framing mode is `hypothesis`, the SoA is provisional and controls may be `planned` — but a control may never be marked `implemented` on the strength of an intention.

---

## Entry criteria

- Prompt 02A tier, obligation register, and AIMS scope exist.
- Prompt 06A threat model, entitlement boundary, tool and approval matrices exist.
- Prompt 07 ADRs and architecture review status (`pass` | `conditional`) exist.
- Accountable role from Prompt 02A is named, or carried as `TBD` with an owner.

---

## Produce

### A. Statement of Applicability (ISO/IEC 42001 Annex A)

One row per Annex A control. Exclusion is legitimate; **unjustified exclusion is not**.

| Control ref | Control | Applicable? | Justification | Implementation (where) | Status | Evidence artefact | Owner |
|---|---|---|---|---|---|---|---|
| A.x.x | | yes / no | why included or excluded | zone / container / ADR / process | planned / implemented / not-applicable | what an auditor would read | role |

Rules:
- Every `no` carries a justification tied to the AIMS scope from Prompt 02A — not "not relevant".
- Every `yes` names an implementation **and** an evidence artefact. A `yes` with neither is an open gap, recorded as `UNKNOWN — owner: <role> · resolves by: <trigger>`.
- Organisational controls (policy, roles, competence, supplier management) are as in-scope as technical ones. Do not fill only the technical rows.

### B. EU AI Act conformance map (high-risk only)

Skip with an explicit `N/A — tier is <tier>` if Prompt 02A did not classify high-risk. If it did:

| Article | Requirement | How met | Artefact | Gap |
|---|---|---|---|---|
| Art. 9 | Risk management system across the lifecycle | | | |
| Art. 10 | Data and data governance (relevance, representativeness, bias examination) | | | |
| Art. 11 | Technical documentation (Annex IV) | | | |
| Art. 12 | Record-keeping / automatic logging | | | |
| Art. 13 | Transparency and information to deployers | | | |
| Art. 14 | Human oversight — effective, by natural persons | | | |
| Art. 15 | Accuracy, robustness and cybersecurity | | | |

Where the organisation is a **deployer**, add Art. 26 obligations and, where applicable, the **Art. 27 fundamental rights impact assessment**. Note the downstream duties that follow if the system is placed on the market: conformity assessment (Art. 43), EU declaration of conformity (Art. 47), CE marking (Art. 48), registration (Art. 49), post-market monitoring plan (Art. 72), and serious-incident reporting (Art. 73). Mark each `in scope now` / `later, at <milestone>` / `N/A`.

Cross-check each row against the binding date in the Prompt 02A obligation register. A control that is not required until 2 Dec 2027 is still recorded — with its date, not as an omission.

### C. AI system impact assessment (clause 6.1.4 / 8.4)

Required where Prompt 02A set the trigger. Cover:

- **Affected individuals and groups** — including those who are not users.
- **Potential harms** — physical, financial, psychological, societal, fundamental rights, environmental.
- **Differential impact** — which groups bear more risk, and how that was examined rather than assumed.
- **Error asymmetry** — is a false negative worse than a false positive, and does the design reflect that? State the direction explicitly.
- **Remedy and contestability** — how an affected person learns a decision involved AI, and how they challenge it.
- **Residual impact** — accepted by whom, on what basis, revisited when.

Where data to assess an impact does not exist, record `inconclusive — evidence required` and link the Prompt 01 acquisition backlog item. Do not assess by assertion.

### D. Control-to-decision traceability

| Obligation (02A) | Control (SoA ref) | Enforcement point (06A) | ADR (07) | Contract owner (08) | Verification (12) |
|---|---|---|---|---|---|

This is the row that makes the pack defensible: an obligation with no control, a control with no enforcement point, or a control with no verification route are each a finding. Flag orphans explicitly rather than leaving the row blank.

### E. Governance operating model (clauses 9–10)

- **Monitoring and measurement** (9.1) — which metrics, which owner, what threshold.
- **Internal audit** (9.2) — scope and cadence.
- **Management review** (9.3) — inputs, frequency, who attends.
- **Nonconformity and corrective action** (10.2) — the route a failed control takes.
- **Certification cadence**, if pursued — first surveillance audit at 12 months, second at 24, recertification at 36.

Name owners. An unowned control is documentation, not governance.

### F. Compliance gate

State one of:

- `cleared` — controls designed, owners named, gaps carry owners and triggers.
- `conditional` — proceed with named conditions carried into Prompt 08 contracts and Prompt 10 tasks.
- `blocked` — a required control has no implementation route, or a prohibited practice surfaced. Stop and escalate.

Under `hypothesis` / `provisional`, prefer `conditional` unless evidence supports `cleared`. **Prompt 08 entry requires `cleared` or `conditional`.**

### Lean / DMAIC lens (spine — thin)

**DMAIC focus this stage:** **Control** (standards, owners, audit cadence) + **Measure** (conformance evidence).

In `dmaic_lens.md` (short), record:

1. Which controls are measurable Control metrics for Prompt 09 and Prompt 12, and which are only documents?
2. Where do overlapping controls duplicate effort across zones (**Extra processing**) versus enforce once?
3. Evidence that must be captured automatically at build time so compliance is not retrofitted later as rework.
4. Controls with no named owner — governance waste, and the single most common cause of a failed audit.

---

## Exit criteria (handoff to Prompt 08)

- [ ] Statement of Applicability covers every Annex A control with an applicability decision and justification.
- [ ] Every applicable control names an implementation, an evidence artefact, and an owner — or is recorded as an `UNKNOWN` gap with owner and trigger.
- [ ] EU AI Act Art. 8–15 conformance map is complete, or explicitly `N/A` with the tier stated.
- [ ] AI system impact assessment exists where triggered, including error asymmetry and contestability.
- [ ] Control-to-decision traceability has no unflagged orphans.
- [ ] Governance operating model names monitoring, audit, review, and corrective-action owners.
- [ ] Compliance gate decision is `cleared` or `conditional` (not `blocked`).
- [ ] Conditions are carried forward to Prompt 08 contracts and Prompt 09 build constraints.
- [ ] `dmaic_lens.md` is complete (feeds Prompt 09).

---

## Constraints

- Do not mark a control `implemented` at design time; design-time status is `planned`.
- Do not exclude an Annex A control without a justification tied to the declared AIMS scope.
- Do not claim conformance where evidence does not exist — use `UNKNOWN` with an owner; a declared gap is a correct answer and a plausible-sounding claim is a finding.
- Do not verify the built system here — that is Prompt 12.
- Do not redesign architecture; if a control demands a structural change, raise a Prompt 06 / 06A revision and open an ADR.
- Do not let a `blocked` gate pass silently to Prompt 08.
- Do not run full Prompt 09 here.

---

## Output

Write under `participant-outputs-v2/07A-compliance/` **and mirror** to `specs/architecture/`:

- `statement_of_applicability.md`
- `eu_ai_act_conformance.md` (or `N/A` with tier stated)
- `ai_system_impact_assessment.md`
- `control_traceability.md`
- `governance_operating_model.md`
- `compliance_gate.md`
- `dmaic_lens.md`
