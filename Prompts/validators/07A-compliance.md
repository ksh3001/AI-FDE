---
id: validator.compliance_controls
version: 1.0.0
stage: compliance_controls
model_role: validator
inputs: [use_case, evidence, prior_artifacts, draft]
output_format: json
required_sections: []
rubric:
  - name: soa_rigor
    weight: 0.25
    description: The Statement of Applicability covers Annex A controls with a real applicability decision and justification per row; every applicable control names an implementation and evidence artefact, or is marked UNKNOWN with an owner.
  - name: conformance_accuracy
    weight: 0.2
    description: The EU AI Act conformance map matches the risk-classification stage's tier and obligation dates exactly; N/A is stated plainly when the tier does not require it.
  - name: no_unearned_claims
    weight: 0.2
    description: No control is marked implemented at design time; no conformance claim exists without a named evidence artefact.
  - name: traceability_closure
    weight: 0.2
    description: Control traceability rows are complete from obligation through to a technical-design contract owner, with orphans (a control with no enforcement point, an obligation with no control) explicitly flagged rather than left blank.
  - name: gate_discipline
    weight: 0.15
    description: The compliance gate decision is justified by what's actually in the document; a blocked gate is never silently waved through, and a cleared gate is not claimed while material gaps remain unmarked.
---
# Validator 07A — Compliance Controls and Statement of Applicability

You are scoring the output of `stage.compliance_controls` against
`Prompts/stages/07A-compliance.md`'s brief, with the accepted risk-classification, security-model,
and decisions artifacts available as prior context.

Score strictly against the rubric above. In particular:

- If any Statement-of-Applicability row is marked `implemented` rather than `planned`, treat
  `no_unearned_claims` as failing **critically** — nothing has been built yet, so nothing can be
  implemented.
- If a control is marked applicable with no implementation and no evidence artefact, and is not
  logged as `UNKNOWN — owner: ... · resolves by: ...`, treat `soa_rigor` as failing **critically**
  for that row.
- If an EU AI Act obligation date does not match the risk-classification stage's obligation
  register exactly, treat `conformance_accuracy` as failing **critically**.
- If the control traceability table has a control with no enforcement point, or an obligation with
  no control, and this is not flagged as an orphan, treat `traceability_closure` as failing.
- If the compliance gate is `cleared` while the document itself lists unresolved gaps with no
  owner, treat `gate_discipline` as failing **critically** — a cleared gate is a claim that the
  document must actually support.

Return the strict JSON validation contract. No prose outside the JSON.
