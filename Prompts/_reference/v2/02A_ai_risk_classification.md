# Prompt 02A — AI Risk Classification & Governance Scope (Gate)

**Lifecycle stage:** Frame → Govern (regulatory gate before product intent)  
**Framework derived:** EU AI Act (Regulation (EU) 2024/1689) + ISO/IEC 42001:2023 AIMS  
**Core question:** What is this system allowed to be, who is accountable, and what obligations attach?  
**Prerequisites:** Prompt 01 evidence register (constraints register, framing mode); Prompt 02 SCQA/Minto (bounded question, capability-level answer).  
**Primary output type:** Regulatory classification + AIMS scope + obligation register (may be provisional).

---

## Intent

Classify the system **before** the PRD scopes it. Regulatory tier is not a review step at the end — it constrains what Prompt 03 may put in scope, what autonomy Prompt 04 may grant, and which controls Prompts 06A/07A must design.

Reference framing: *compliance outranks feasibility in regulated work — a brilliant system the accountable function will not sign is worth zero.*

This prompt does **not** design controls (that is 06A/07A) and does **not** assess conformity of a built system (that is Prompt 12). It answers: which regime applies, at what tier, by when, and who is accountable.

If Prompt 02 narrative class is `hypothesis`, classification is **provisional** — but the *prohibited-practice check is never provisional*. A prohibited practice is a stop, not a risk.

---

## Entry criteria

- Prompt 02 narrative class is stated (`decision-ready` | `hypothesis`).
- One bounded decision question and capability-level answer (or experiment) exist.
- Prompt 01 constraints register (compliance, security, privacy, residency) is available.
- Intended purpose, deployment geography, and affected persons are known or explicitly Unknown.

---

## Produce

### A. Intended purpose statement (required first)

One paragraph, in regulatory language, stating: what the system does, for whom, in which jurisdictions, over which data subjects, and what decision or output it influences. Classification is meaningless without this — write it before anything below.

State the **role assumed**: provider, deployer, importer, distributor, or authorised representative. If the organisation is both provider and deployer, say so; obligations differ and both apply.

### B. Prohibited-practice check (Art. 5) — blocking

Check the intended purpose against each prohibited practice. Applicable since **2 Feb 2025**.

| Practice | Applies? | Evidence / reasoning |
|---|---|---|
| Subliminal / manipulative or deceptive techniques | yes / no / Unknown | |
| Exploitation of vulnerabilities (age, disability, socio-economic) | | |
| Social scoring | | |
| Individual criminal-offence risk prediction (profiling-based) | | |
| Untargeted facial-image scraping for FR databases | | |
| Emotion inference in workplace or education | | |
| Biometric categorisation inferring sensitive attributes | | |
| Real-time remote biometric identification in public spaces (law enforcement) | | |

**If any is `yes`: stop.** Record `classification: prohibited`, do not proceed to Prompt 03, and escalate. A prohibited practice cannot be mitigated by controls.

### C. High-risk classification (Art. 6 + Annex III)

1. **Annex III route** — is the intended purpose in a listed area? Biometrics; critical infrastructure; education and vocational training; employment, worker management and self-employment access; access to essential private and public services (incl. creditworthiness, insurance pricing, emergency triage); law enforcement; migration, asylum and border control; administration of justice and democratic processes.
2. **Product-safety route** — is the system a safety component of, or itself, a product covered by Union harmonisation legislation in Annex I (machinery, medical devices, vehicles, lifts, toys, …)?
3. **Art. 6(3) derogation** — if Annex III applies, does the system nonetheless perform only a narrow procedural task, improve a prior human activity, detect decision patterns without replacing human assessment, or do preparatory work? If claimed, **document the reasoning and note the registration obligation still applies**. Do not claim the derogation to avoid work.

State the outcome as exactly one of: `prohibited` · `high-risk` · `limited-risk (transparency)` · `minimal-risk` · `GPAI` · `high-risk + GPAI`.

### D. GPAI check (Art. 51–56)

If a general-purpose AI model is placed on the market or integrated: record provider vs downstream-deployer position, whether the model presents **systemic risk**, and which obligations transfer to your organisation versus remain with the upstream model provider. Note contractual evidence you rely on.

### E. Transparency obligations (Art. 50)

Regardless of tier: does the system interact directly with people, generate synthetic content, produce deep fakes, or perform emotion recognition / biometric categorisation? Each triggers a disclosure or machine-readable-marking obligation. Record which apply and what the user-facing disclosure must say.

### F. Obligation register with dates

For the tier established, list the applicable obligations and the date each binds. Do not paraphrase deadlines — anchor them.

| Milestone | Applies from | Relevant to this system? |
|---|---|---|
| Prohibited practices; AI literacy (Art. 4) | 2 Feb 2025 | |
| Governance, national competent authorities, penalties, new GPAI models | 2 Aug 2025 | |
| Most remaining provisions: deployer obligations, post-market monitoring, transparency, enforcement; GPAI enforcement by the Commission | 2 Aug 2026 | |
| Technical transparency solutions for marking AI-generated content | 2 Dec 2026 | |
| GPAI models placed on the market before 2 Aug 2025 | 2 Aug 2027 | |
| Standalone high-risk systems (Annex III use cases) | 2 Dec 2027 | |
| High-risk systems embedded in regulated products (Annex I) | 2 Aug 2028 | |

For `high-risk`, name the Art. 8–15 requirements that will bind (risk management system, data governance, technical documentation, record-keeping, transparency to deployers, human oversight, accuracy/robustness/cybersecurity) — **design happens in 07A, not here.**

### G. ISO/IEC 42001 AIMS scope (clause 4.3)

- **Context and interested parties** (4.1, 4.2) — who is affected, who must be satisfied.
- **AIMS scope statement** (4.3) — what is in and out of the management system for this engagement.
- **AI policy reference** (5.2) and **roles, responsibilities and authorities** (5.3) — name the accountable role, or mark `TBD — owner: <role>` and add to the Prompt 01 acquisition backlog.
- **AI risk assessment** (6.1.2) — top AI risks with likelihood/impact.
- **AI system impact assessment trigger** (6.1.4 / 8.4) — is one required, and who owns it? The assessment itself is executed in 07A.

### H. Risk tier → architecture consequences

Translate the classification into constraints the rest of the chain must obey. This is the load-bearing output.

| Consequence | Value |
|---|---|
| Maximum permitted autonomy | e.g. AI proposes, human decides |
| Decisions the system may never make alone | |
| Human oversight requirement (Art. 14) | who, at what point, seeing what |
| Logging / record-keeping floor (Art. 12) | |
| Explainability floor | what a reviewer or inspector must be able to reconstruct |
| Data residency / transfer limits | |
| Approval routing driven by tier | |

Reference pattern: *risk tier drives approval, logging, routing, and model choice* — and *preserve human ownership for high-impact decisions*.

### Lean / DMAIC lens (spine — thin)

**DMAIC focus this stage:** **Define** (the boundary of permitted improvement) + early **Control** (obligations that become control requirements).

In `dmaic_lens.md` (short), record:

1. Which obligations are Control requirements that Prompt 09 must carry into its Control plan?
2. Which automation ideas are ruled out by tier — and what waste does *not* get removed as a result (name it honestly)?
3. Does the oversight requirement risk **Human-review waste** (reviewing everything) — where can tiering keep low-risk flows out of the queue?
4. Compliance evidence that must be captured from day one, so it is not retrofitted as Extra processing later.

---

## Exit criteria (handoff to Prompt 03)

- [ ] Intended purpose and role (provider / deployer / both) are stated.
- [ ] Prohibited-practice check completed; if any `yes`, the chain is stopped and escalated.
- [ ] Classification is exactly one declared tier, with the Art. 6 / Annex III reasoning shown.
- [ ] GPAI position and Art. 50 transparency obligations are recorded (or explicitly N/A).
- [ ] Obligation register lists applicable duties with binding dates.
- [ ] AIMS scope, accountable role (or `TBD` with owner), and impact-assessment trigger are recorded.
- [ ] Risk tier → architecture consequences table is complete — Prompt 03 can scope against it.
- [ ] Provisional status declared if narrative class is `hypothesis` (prohibited check excepted).
- [ ] `dmaic_lens.md` is complete (feeds Prompt 09).

---

## Constraints

- Do not design controls, zones, or mitigations here — that is 06A and 07A.
- Do not assess a built system — that is Prompt 12.
- Do not claim the Art. 6(3) derogation without written reasoning against all four conditions.
- Do not soften a classification because it makes the project harder; record the tier and let scope adapt.
- Do not treat `Unknown` jurisdiction, data subjects, or intended purpose as `minimal-risk` by default — Unknown goes to the acquisition backlog and the tier stays provisional at the higher plausible level.
- Do not paraphrase regulatory deadlines from memory; carry the dates in the table above.
- Do not run full Prompt 09 here.

---

## Output

Write under `participant-outputs-v2/02A-risk-classification/`:

- `intended_purpose.md`
- `risk_classification.md` (prohibited check, tier, reasoning, GPAI, Art. 50)
- `obligation_register.md`
- `aims_scope.md` (ISO 42001 clause 4–6 scoping)
- `tier_architecture_consequences.md`
- `dmaic_lens.md`
