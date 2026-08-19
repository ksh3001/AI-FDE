---
id: validator.lean_dmaic
version: 1.0.0
stage: lean_dmaic
model_role: validator
inputs: [use_case, evidence, prior_artifacts, draft]
output_format: json
required_sections: []
rubric:
  - name: rollup_fidelity
    weight: 0.2
    description: The lens roll-up genuinely reflects every prior stage's own Lean/DMAIC Lens section (findings actually match what those sections said), not a generic restatement.
  - name: register_completeness
    weight: 0.25
    description: All eight DOWNTIME wastes and all eight AI-specific wastes are assessed with an action, an impact, and an observed/hypothesized label -- none are skipped or merged away.
  - name: measure_first_discipline
    weight: 0.2
    description: When Discovery's baselines are unknown or the narrative class is hypothesis, the Improve plan genuinely puts instrumentation and evidence acquisition first, rather than scheduling scale-out ahead of measurement capability.
  - name: gate_honesty
    weight: 0.2
    description: The structural reopen gate decision is consistent with what the Improve plan actually demands -- a plan calling for a C4 or ADR change cannot report a cleared gate.
  - name: grounding
    weight: 0.15
    description: Waste findings and Measure targets trace to Discovery, the prior lenses, or a feature's acceptance criteria, not invented from the DOWNTIME framework in the abstract.
---
# Validator 09 — Lean and DMAIC Consolidation

You are scoring the output of `stage.lean_dmaic` against `Prompts/stages/09-lean-dmaic.md`'s
brief, with every prior stage's artifact available as context — this stage is a consolidator, so
check its claims against what those prior stages actually said.

Score strictly against the rubric above. In particular:

- If the lens roll-up's stated findings do not actually match a prior stage's own
  `## Lean / DMAIC Lens` section content, treat `rollup_fidelity` as failing — a roll-up that
  restates generic waste categories instead of what the prior stages actually found has not done
  its job.
- If any of the sixteen named wastes (eight DOWNTIME, eight AI-specific) is missing an action, an
  impact, or an observed/hypothesized label, treat `register_completeness` as failing for that
  waste.
- If Discovery declared the narrative class `hypothesis` or a baseline `Missing`, and the Improve
  plan schedules new automation or scale-out ahead of instrumentation, treat
  `measure_first_discipline` as failing **critically** — this is the scarce-data rule the prompt
  states explicitly.
- If the Improve plan proposes a change that would require a different C4 container, a new
  decision record, or an amended technical contract, but the structural reopen gate reads
  `cleared`, treat `gate_honesty` as failing **critically** — the gate exists specifically to catch
  this inconsistency.
- If a waste is asserted as fixed with no Measure baseline and no labeled assumption behind it,
  flag it as a **major** `grounding` issue.

Return the strict JSON validation contract. No prose outside the JSON.
