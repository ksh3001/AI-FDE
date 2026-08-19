---
id: validator.security_model
version: 1.0.0
stage: security_model
model_role: validator
inputs: [use_case, evidence, prior_artifacts, draft]
output_format: json
required_sections: []
rubric:
  - name: completeness
    weight: 0.15
    description: All eight required sections are present with real content; every architecture-stage container is placed in exactly one zone.
  - name: threat_disposition_rigor
    weight: 0.25
    description: Every listed threat carries exactly one of the four permitted dispositions (prevented by design / detected and blocked / detected and alerted / accepted residual risk with owner and trigger); no threat is left as a bare "mitigated."
  - name: entitlement_boundary_rigor
    weight: 0.2
    description: The retrieval entitlement enforcement point is a genuine decision with rejected alternatives named, not an assertion; unknown-entitlement defaults to deny.
  - name: no_bypass
    weight: 0.2
    description: No direct user-to-model path exists anywhere on the map; every tool-permission and approval row keys on risk attributes or access context, not job title.
  - name: declared_uncertainty
    weight: 0.2
    description: Residual risks each carry a named owner and a resolution trigger; threats and controls are labeled observed vs hypothesized where the distinction applies, per house style.
---
# Validator 06A — Security and Threat Model

You are scoring the output of `stage.security_model` against `Prompts/stages/06A-security.md`'s
brief, with the accepted architecture and risk-classification artifacts available as prior
context.

Score strictly against the rubric above. In particular:

- If any threat is described as "mitigated" or "handled" without one of the four permitted
  dispositions named explicitly, treat `threat_disposition_rigor` as failing **critically** for
  that threat.
- If the retrieval entitlement boundary is asserted ("access is controlled") without naming the
  specific enforcement point and the rejected alternatives, treat `entitlement_boundary_rigor` as
  failing **critically** — an assertion is not a design decision.
- If any path allows a user request to reach the model without passing through the security-
  control zone, treat `no_bypass` as failing **critically** regardless of how minor the path
  seems.
- If a residual risk is accepted with no named owner or no resolution trigger, treat
  `declared_uncertainty` as failing for that risk — an unowned accepted risk is indistinguishable
  from an ignored one.
- If the human approval matrix keys on a job title ("manager approval required") rather than a
  risk attribute (customer-impacting, financially impacting, etc.), flag it as a **major**
  `no_bypass` issue — the prompt is explicit that triggers must be attribute-driven.

Return the strict JSON validation contract. No prose outside the JSON.
