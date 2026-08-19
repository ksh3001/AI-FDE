---
id: stage.risk_classification
version: 1.0.0
stage: risk_classification
model_role: generator
inputs: [use_case, evidence, prior_artifacts]
output_format: markdown
required_sections:
  - Intended Purpose
  - Prohibited-Practice Check
  - Risk Classification
  - GPAI Position
  - Transparency Obligations
  - Obligation Register
  - AIMS Scope
  - Risk Tier and Architecture Consequences
  - Lean / DMAIC Lens
---
# Prompt 02A — AI Risk Classification & Governance Scope

Classify `{SYSTEM}` under the EU AI Act (Regulation (EU) 2024/1689) and scope it under ISO/IEC
42001:2023, using the accepted Discovery and SCQA artifacts as your evidence base. Do this
**before** any target architecture is designed — the tier constrains what later design work may
propose, not the other way around.

Compliance outranks feasibility in regulated work: a system the accountable function will not
sign is worth zero, however well it is built. If evidence for a material fact below is genuinely
missing rather than merely unstated, mark it `UNKNOWN — owner: <role> · resolves by: <trigger>`
per house style — do not default an unknown jurisdiction, data-subject population, or intended
purpose to `minimal-risk` to make the classification easier.

## Intended Purpose

One paragraph, in regulatory language: what the system does, for whom, in which jurisdictions,
over which data subjects, and what decision or output it influences. State the role assumed —
provider, deployer, importer, distributor, or authorised representative (or more than one, if
so).

## Prohibited-Practice Check

Check the intended purpose against every Art. 5 prohibited practice (applicable since
2 Feb 2025), as a table with one row per practice: subliminal or manipulative/deceptive
techniques; exploitation of vulnerabilities (age, disability, socio-economic); social scoring;
individual criminal-offence risk prediction from profiling; untargeted facial-image scraping for
facial-recognition databases; emotion inference in workplace or education; biometric
categorisation inferring sensitive attributes; real-time remote biometric identification in
public spaces for law enforcement. For each: `applies` (yes / no / Unknown) and the reasoning.

**If any row is `yes`: stop.** State the classification as `prohibited`, and that no further
design work should proceed until this is resolved. A prohibited practice cannot be mitigated by
controls — do not let a later section soften this.

## Risk Classification

Determine, in order: (1) the **Annex III route** — is the intended purpose in a listed
high-risk area (biometrics; critical infrastructure; education and vocational training;
employment and worker management; access to essential private/public services including
creditworthiness, insurance pricing, emergency triage; law enforcement; migration, asylum and
border control; administration of justice and democratic processes)? (2) the **product-safety
route** — is the system a safety component of, or itself, a product under Annex I Union
harmonisation legislation (machinery, medical devices, vehicles, lifts, toys, …)? (3) if Annex III
applies, does the **Art. 6(3) derogation** genuinely apply — narrow procedural task, improving a
prior human activity, detecting patterns without replacing human assessment, or preparatory work?
If claimed, document the reasoning against all four conditions and note that the registration
obligation still applies regardless.

State the outcome as **exactly one** of: `prohibited` · `high-risk` · `limited-risk (transparency)`
· `minimal-risk` · `GPAI` · `high-risk + GPAI`, with the reasoning that produced it.

## GPAI Position

If a general-purpose AI model is placed on the market or integrated into this system: record
whether the organisation is the model provider or a downstream deployer, whether the model
presents systemic risk, and which obligations transfer to this organisation versus remain with
the upstream provider. If no GPAI model is involved, state that plainly rather than omitting the
section.

## Transparency Obligations

Regardless of tier: does the system interact directly with people, generate synthetic content,
produce deepfakes, or perform emotion recognition or biometric categorisation? Each triggers an
Art. 50 disclosure or machine-readable-marking obligation. Record which apply and what the
user-facing disclosure must say; if none apply, state that.

## Obligation Register

List the obligations that bind given the tier above, each against its binding date. Anchor every
date to this table — do not paraphrase a milestone from memory:

| Milestone | Applies from |
|---|---|
| Prohibited practices; AI literacy (Art. 4) | 2 Feb 2025 |
| Governance, national competent authorities, penalties, new GPAI models | 2 Aug 2025 |
| Most remaining provisions: deployer obligations, post-market monitoring, transparency, enforcement; GPAI enforcement by the Commission | 2 Aug 2026 |
| Technical transparency solutions for marking AI-generated content | 2 Dec 2026 |
| GPAI models placed on the market before 2 Aug 2025 | 2 Aug 2027 |
| Standalone high-risk systems (Annex III use cases) | 2 Dec 2027 |
| High-risk systems embedded in regulated products (Annex I) | 2 Aug 2028 |

For each row, state whether it is relevant to this system. If `high-risk`, also name which
Art. 8–15 requirements will bind (risk management system, data governance, technical
documentation, record-keeping, transparency to deployers, human oversight,
accuracy/robustness/cybersecurity) — naming them here is enough; designing how they are met is
later design work, not this stage.

## AIMS Scope

Scope the ISO/IEC 42001 AI management system for this engagement: context and interested parties
(clauses 4.1–4.2); the AIMS scope statement (4.3) — what is in and out; the accountable role for
AI policy and roles/responsibilities (5.2–5.3), or `TBD — owner: <role>` if not yet named; the top
AI risks with likelihood and impact (6.1.2); and whether an AI system impact assessment is
triggered (6.1.4 / 8.4) and who would own it.

## Risk Tier and Architecture Consequences

Translate the classification into constraints later design work must obey — this is the
load-bearing output of this stage. Cover, at minimum: the maximum permitted autonomy (e.g. "AI
proposes, human decides"); decisions the system may never make alone; the human-oversight
requirement (Art. 14) — who, at what point, seeing what; the logging and record-keeping floor
(Art. 12); the explainability floor — what a reviewer or inspector must be able to reconstruct;
data residency or transfer limits; and how approval routing should be driven by tier. Risk tier
should drive approval, logging, routing, and model choice from here on — and human ownership of
high-impact decisions is preserved regardless of tier.

## Lean / DMAIC Lens

This stage's focus is **Define** (the boundary of permitted improvement) and early **Control**
(obligations that become control requirements later). Record: which obligations above are Control
requirements that later consolidation work must carry forward; which automation ideas are ruled
out by the tier, and what waste does *not* get removed as a result — name it honestly rather than
skip it; whether the oversight requirement risks human-review waste (reviewing everything), and
where tiering could keep low-risk flows out of a review queue; and what compliance evidence must
be captured from the start so it is not retrofitted later as rework.

Use exactly these `##` section headings, in this order: Intended Purpose, Prohibited-Practice
Check, Risk Classification, GPAI Position, Transparency Obligations, Obligation Register, AIMS
Scope, Risk Tier and Architecture Consequences, Lean / DMAIC Lens.
