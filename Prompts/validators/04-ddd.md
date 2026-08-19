---
id: validator.domain_model
version: 2.0.0
stage: domain_model
model_role: validator
inputs: [use_case, evidence, prior_artifacts, draft]
output_format: json
required_sections: []
rubric:
  - name: completeness
    weight: 0.2
    description: All seven required sections are present with real, specific content covering ubiquitous language, bounded contexts, domain events/model, rules-vs-AI-vs-HITL boundaries, and the governed workflow.
  - name: grounding
    weight: 0.2
    description: Bounded contexts, events, and invariants trace to the use case, evidence, or prior artifacts; the domain is not organised around technical layers or dataset/API names.
  - name: rules_ai_hitl_discipline
    weight: 0.25
    description: The boundary between deterministic rules, AI reasoning, and required human review is explicit and consistent with the risk-classification stage's permitted-autonomy consequences; nothing here grants the AI more autonomy than that stage allows.
  - name: artifact_status_honesty
    weight: 0.15
    description: The declared artifact status (stable/provisional) matches the actual state of the narrative class and open ubiquitous-language questions; a provisional model is not presented as settled domain truth.
  - name: structure
    weight: 0.2
    description: Bounded contexts have named owners or an explicit TBD with an owner; the context map is an actual fenced plantuml diagram (not a prose list standing in for one) with real relationship types; headings match house style.
---
# Validator 04 — Domain-Driven Design for Gen AI

You are scoring the output of `stage.domain_model` against `Prompts/stages/04-ddd.md`'s brief,
with the accepted Discovery, SCQA, PRD, and risk-classification artifacts available as prior
context.

Score strictly against the rubric above. In particular:

- If the "Rules, AI and HITL Boundaries" section grants the AI more autonomy than the
  risk-classification stage's "Risk Tier and Architecture Consequences" table permits (e.g. an AI
  deciding alone where that table requires a human decision), treat `rules_ai_hitl_discipline` as
  failing **critically** — this is the single most important check for this stage, since every
  later design stage inherits this boundary.
- If a bounded context has no owner and no `TBD — owner: <role>` marker, treat `structure` as
  failing for that context.
- If the context map is prose or a bulleted list instead of a fenced ```plantuml``` diagram, treat
  `structure` as failing — a diagram is not optional decoration here, per house style.
- If the artifact status is `stable` while the narrative class is `hypothesis` with no documented
  upgrade, treat `artifact_status_honesty` as failing **critically**.
- If the domain model is organised around a dataset name, an API endpoint, or a technology layer
  rather than business meaning, flag it as a **major** `grounding` issue — the prompt explicitly
  forbids this.
- If a C4 diagram, a full ADR, or detailed feature flows appear in this draft, treat
  `completeness` as failing for scope discipline — those belong to later stages, and their
  presence here usually means the domain work itself was skipped.

Return the strict JSON validation contract. No prose outside the JSON.
