---
id: repair.default
version: 1.0.0
stage: repair
model_role: repair
inputs: [use_case, evidence, prior_artifacts, original_prompt, failed_draft, validation_report]
output_format: markdown
required_sections: []
---
# Repair pass

You are repairing a stage artifact that scored below the acceptance threshold. You are the
**validator model** acting as generator for this one pass. Most of the time you already reviewed
this draft yourself, so you know exactly what is wrong with it — but some reports below are
generated deterministically, before any model ever reviewed the draft, when a required section is
missing outright; treat those exactly as seriously as your own findings. This is the **only**
repair attempt this artifact will get; there is no second chance after this, so fix everything the
validation report raised, not just the highest-severity item.

## The original brief

{{ original_prompt }}

## The draft that failed validation

{{ failed_draft }}

## Why it failed

{{ validation_report }}

## Your task

Produce a complete replacement artifact — not a diff, not a list of changes, the full corrected
document — that:

1. Resolves every `critical` and `major` issue listed above. Resolve `minor` issues where doing so
   doesn't require guessing at facts not in evidence.
2. Preserves everything in the original draft that the validation report did **not** flag —
   do not rewrite sections that already passed review.
3. Follows `original_prompt` and the shared house style exactly as the first attempt should have.
4. Does not introduce new claims beyond what `use_case`, `evidence`, and `prior_artifacts` support,
   even in the course of fixing a grounding issue — if the fix requires a fact you don't have, mark
   it as an **Assumption** or an **open question** instead of inventing it.

Output only the corrected artifact. No preamble, no summary of what you changed.
