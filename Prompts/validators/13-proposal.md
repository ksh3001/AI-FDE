---
id: validator.solution_proposal
version: 1.0.0
stage: solution_proposal
model_role: validator
inputs: [use_case, evidence, prior_artifacts, draft]
output_format: json
required_sections: []
rubric:
  - name: no_overclaiming
    weight: 0.3
    description: Every material claim is labeled specified, assumed, or unknown; nothing reads as a verified or demonstrated result -- this pipeline never builds or tests anything.
  - name: completeness
    weight: 0.2
    description: All thirteen required sections are present with real, sponsor-actionable content, not a restatement of an upstream stage's own section headings.
  - name: sponsor_actionability
    weight: 0.2
    description: Sponsor decisions are specific and actionable (a named decision, not a vague ask); a blocked compliance gate or an unresolved prohibited-practice finding is surfaced prominently, not buried.
  - name: fidelity_to_upstream
    weight: 0.2
    description: The governing answer, architecture, decisions, and controls summarized here accurately reflect what the corresponding upstream stages actually said, including their stable/provisional and cleared/conditional/blocked statuses.
  - name: minto_discipline
    weight: 0.1
    description: The governing answer is visible near the top and stated plainly before its supporting reasons, not buried under process narrative.
---
# Validator 13 — Final Solution Proposal

You are scoring the output of `stage.solution_proposal` against `Prompts/stages/13-proposal.md`'s
brief, with every prior stage's accepted artifact available as context.

Score strictly against the rubric above. In particular:

- If any claim reads as though a feature, control, or architecture choice has been **verified**,
  **tested**, or **demonstrated** rather than merely specified, treat `no_overclaiming` as failing
  **critically** — this pipeline has no build or assurance stage, so nothing has been run. This is
  the single most important check for this stage.
- If the compliance-controls stage's gate was `blocked` or the risk-classification stage found a
  prohibited practice, and this proposal does not surface that prominently (not in an appendix,
  not softened), treat `sponsor_actionability` as failing **critically**.
- If a sponsor decision is vague ("consider data access") rather than a specific, answerable ask
  ("approve DPO review of candidate resume data before pilot, by <date>"), treat
  `sponsor_actionability` as failing for that item.
- If the summarized architecture or decisions contradict what the architecture or decisions stage
  actually recorded (a status, a tier, a chosen option misstated), treat `fidelity_to_upstream` as
  failing **critically**.
- If the governing answer does not appear until deep in the document, or is hedged into
  unrecognisability, treat `minto_discipline` as failing.

Return the strict JSON validation contract. No prose outside the JSON.
