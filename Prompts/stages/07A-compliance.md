---
id: stage.compliance_controls
version: 1.0.0
stage: compliance_controls
model_role: generator
inputs: [use_case, evidence, prior_artifacts]
output_format: markdown
required_sections:
  - Statement of Applicability
  - EU AI Act Conformance Map
  - AI System Impact Assessment
  - Control Traceability
  - Governance Operating Model
  - Compliance Gate
  - Lean / DMAIC Lens
---
# Prompt 07A — Compliance Controls and Statement of Applicability

Convert the obligations the risk-classification stage established into named controls, with named
implementations and named evidence. That stage said which duties attach; the security-model stage
designed the technical enforcement; this stage closes the loop — every obligation maps to a
control, every control maps to where it lives, and every control names the artefact that would
prove it to an auditor.

The failure mode this stage exists to prevent is checklist theatre: passing every framework
question on paper while the real risk — no ground truth, no named owner, no evidence trail — is
not on the checklist. A control with no implementation and no evidence is a claim, not a control.

This stage is design-time only. Whether a control actually works once the system is built is
outside this pipeline's scope — what matters here is that every claim is either backed by a real
implementation and evidence artefact, or is honestly marked as a gap with an owner.

## Statement of Applicability

One row per ISO/IEC 42001 Annex A control: whether it applies, the justification either way, where
it is implemented (a zone, a container, a decision record, a process), its status (`planned` |
`not-applicable` — never `implemented` at this stage, since nothing has been built yet), the
evidence artefact an auditor would read, and the owner. Every `no` needs a justification tied to
the AIMS scope the risk-classification stage set, not "not relevant." Every `yes` needs an
implementation and an evidence artefact — a `yes` with neither is an open gap, recorded as
`UNKNOWN — owner: <role> · resolves by: <trigger>` per house style. Organisational controls
(policy, roles, competence, supplier management) are as in scope as technical ones — do not fill
only the technical rows.

## EU AI Act Conformance Map

State `N/A — tier is <tier>` if the risk-classification stage did not reach `high-risk`. If it
did, map Art. 9–15 (risk management system, data governance, technical documentation,
record-keeping, transparency to deployers, human oversight, accuracy/robustness/cybersecurity):
how each is met, the evidence artefact, and any gap. Where the organisation is a deployer, add
Art. 26 obligations and, where applicable, the Art. 27 fundamental-rights impact assessment. Note
downstream duties that follow if the system is placed on the market — conformity assessment,
declaration of conformity, CE marking, registration, post-market monitoring plan, serious-incident
reporting — each marked `in scope now` / `later, at <milestone>` / `N/A`. Cross-check every row
against the binding date in the risk-classification stage's obligation register; a control not
required until a later milestone is still recorded, with its date, not omitted.

## AI System Impact Assessment

Required if the risk-classification stage triggered it. Cover: the affected individuals and
groups, including those who are not users; potential harms — physical, financial, psychological,
societal, fundamental-rights, environmental; differential impact — which groups bear more risk,
and how that was actually examined rather than assumed; error asymmetry — state plainly whether a
false negative or a false positive is worse here, and whether the design reflects that; remedy and
contestability — how an affected person learns AI was involved, and how they challenge a decision;
and residual impact — accepted by whom, on what basis, revisited when. Where the evidence to
assess an impact does not exist, record `inconclusive — evidence required` and link the relevant
Discovery acquisition-backlog item; do not assess by assertion.

## Control Traceability

One row per obligation: the risk-classification obligation it comes from, the Statement-of-
Applicability control reference, the security-model enforcement point, the decision record that
authorises it, and the technical-design contract that will implement it. This is the row that
makes the pack defensible — an obligation with no control, a control with no enforcement point, or
a control with no eventual verification path are each a finding; flag orphans explicitly rather
than leaving a cell blank.

## Governance Operating Model

Monitoring and measurement — which metrics, which owner, what threshold. Internal audit — scope
and cadence. Management review — inputs, frequency, who attends. Nonconformity and corrective
action — the route a failed control takes. Certification cadence, if pursued. Name owners
throughout — an unowned control is documentation, not governance.

## Compliance Gate

State exactly one: `cleared` — controls designed, owners named, gaps carry owners and triggers;
`conditional` — proceed with named conditions carried into the technical-design stage; `blocked` —
a required control has no implementation route, or a prohibited practice surfaced upstream. Under
`provisional` or `hypothesis` artifact status, prefer `conditional` unless the evidence genuinely
supports `cleared`.

## Lean / DMAIC Lens

This stage's focus is **Control** (standards, owners, audit cadence) and **Measure** (conformance
evidence). Record: which controls are measurable Control metrics versus documents only; where
overlapping controls duplicate effort across zones rather than enforcing once; what evidence must
be captured automatically at build time so compliance is not retrofitted later as rework; and
which controls have no named owner — the single most common cause of a failed audit.

Do not mark a control `implemented` at design time. Do not exclude an Annex A control without a
justification tied to the declared AIMS scope. Do not claim conformance where evidence does not
exist — use `UNKNOWN` with an owner; a declared gap is a correct answer, and a plausible-sounding
claim with no evidence is a finding. Do not redesign architecture here — if a control demands a
structural change, raise it back to the architecture or security-model stage. Do not let a
`blocked` gate pass silently into the next stage.

Use exactly these `##` section headings, in this order: Statement of Applicability, EU AI Act
Conformance Map, AI System Impact Assessment, Control Traceability, Governance Operating Model,
Compliance Gate, Lean / DMAIC Lens.
