# AI-FDE Pipeline Upgrade Plan

Migration from the current 5-stage pipeline (Discovery → ADR) to a 13-stage design and
governance chain (Discovery → Solution Proposal), with Lean/DMAIC as the operating spine and
EU AI Act / ISO 42001 governance added.

**Scope: design and governance only.** Prompt 11 (AI coding) is deleted; Prompts 10
(implementation tasks) and 12 (assurance) are out of scope. The chain ends at Prompt 09's
`structural_reopen` gate — the boundary the library itself defines as the entry to
implementation — and closes with the Prompt 13 sponsor proposal.

Status: **approved plan, not yet started.**

---

## 1. Decisions settled

| Decision | Outcome |
|---|---|
| Lean/DMAIC placement | Thin `dmaic_lens` section in **every** stage, consolidated by the Prompt 09 workshop. Authored into the v2 prompts — not a generic house-style footer. |
| Multi-file prompt outputs | **Enforced H2 sections** in one artifact per stage. Wires up the existing-but-dead `required_sections` field. No data-model change. |
| Missing prompts | Prompts 01–09 and 13 supplied by the user. **02A / 06A / 07A** authored from the deck — Day 22 (ISO 42001 + EU AI Act), Day 13 (Aarohan zones and ADR register). |
| Stage numbering | **Suffixed insertion** (`02A`, `06A`, `07A`) so every cross-reference in the user prompts stays valid. |
| Prompt 11 (AI coding) | **Deleted.** The pipeline writes specifications, not source. |
| Prompts 10, 12 | **Out of scope.** 10 is the coding-agent handoff; 12 audits a running system. Both are downstream of a build that no longer exists. |
| Prompt 13 | **Kept as terminal stage.** The only sponsor-facing artifact; 17 of its 20 required items come from 01–09. |
| Validators | Derived from each prompt's *Exit criteria* → weighted rubric, and *Constraints* → critical-severity checks. |
| Approval gates | **Six mandatory, seven auto-approve-on-pass.** See §4.1. |
| Build sequencing | **Vertical slice first.** One new stage proven end to end before the bulk migration. See §5. |

## 2. Target pipeline — 13 stages

| order | prompt | stage id | artifact | approval |
|---|---|---|---|---|
| 1 | 01 | `discovery` | `01-discovery.md` | **manual** — framing mode |
| 2 | 02 | `scqa` | `02-scqa.md` | auto |
| 3 | **02A** | `risk_classification` | `03-risk.md` | **manual** — risk tier |
| 4 | 03 | `prd` | `04-prd.md` | auto |
| 5 | 04 | `domain_model` | `05-ddd.md` | auto |
| 6 | 05 | `feature_specs` | `06-features.md` | auto |
| 7 | 06 | `architecture` | `07-c4.md` | auto |
| 8 | **06A** | `security_model` | `08-security.md` | auto |
| 9 | 07 | `decisions` | `09-adr.md` | **manual** — review verdict |
| 10 | **07A** | `compliance_controls` | `10-compliance.md` | **manual** — compliance gate |
| 11 | 08 | `technical_design` | `11-technical.md` | auto |
| 12 | 09 | `lean_dmaic` | `12-lean-dmaic.md` | **manual** — structural reopen |
| 13 | 13 | `solution_proposal` | `13-proposal.md` | **manual** — sponsor sign-off |

New prompts live in `Prompts/_reference/v2/`; the user's join them there. The registry loads
only `_shared`, `stages`, `validators`, `repair` (`registry.py` `_LOADED_SUBDIRS`), so
`_reference/` never affects startup.

### Why the chain ends at 09

Prompt 09's structural-change gate states *"Prompt 10 entry requires `cleared`."* That gate is
the design→build boundary the library draws for itself. Ending there is not an arbitrary cut —
and the gate gains meaning rather than losing it: `blocked` now means *this design is not ready
to put in front of a sponsor.*

Prompt 09 is also a synthesis rather than a fragment — `lens_rollup.md` consolidates every
`dmaic_lens` from 01–08 — so the design chain closes on the DMAIC spine being pulled together.

### DMAIC coverage

Define 02·03 · Measure 01·03 · Analyze 04·05·07 · Improve 05·06·08, all consolidated in **09**
(full DOWNTIME and AI-specific waste registers, DMAIC plan, structural-reopen gate) and carried
to sponsors in **13**. Governance additions: 02A Define+Control, 06A Improve+Control,
07A Control+Measure.

**Accepted limitation:** with no build, Control is *planned* and never *verified*, and every
AI-specific waste (token, retrieval, model, evaluation, observability) stays `hypothesized`
rather than `observed` — those are runtime phenomena. Prompt 09's own observed/hypothesized
labelling makes this visible rather than hiding it.

## 3. Prompt rework required

Dropping 10, 11 and 12 leaves dangling references. Two need real edits; the rest are cosmetic.

### Prompt 13 — moderate rework *(blocks the final stage)*

Written to synthesise a build and an assurance report. Needs:

- **Prerequisites** — "Prompts 01–12, especially Assurance" → 01–09.
- **Entry criteria** — drop "Evaluation report and residual risks exist" and "PoC vs production
  gaps are listed".
- **Produce §6, §8** — "AC results" and "specified **vs verified**" → `specified | not verified`.
- **DMAIC lens §3, §5** — Control owners come from 07A and 09, not `production_readiness.md`;
  drop pilot learnings.
- **Explicit labelling** — "Demonstrated in PoC vs Required for production" → `specified` /
  `assumed` / `unknown`. Without this the proposal implies verification that never happened.
- **Exit criteria** — drop the four items referencing Assurance findings, PoC-vs-production and
  DDD stage 16 handover.

### Prompt 09 — light rework

Exit criteria say "handoff to Prompt 10" and "Prompt 10 task order can prioritize…";
`structural_reopen` says "Prompt 10 entry requires `cleared`". Reword so 09 hands off to 13 and
the gate reads as the terminal design gate.

### Cosmetic — tidy during migration

`04` ("executed in Prompt 11 / 12"), `07` ("detail that belongs in Prompt 11", "flagged for
Prompt 13" — still valid), `08` ("handoff to Prompt 09" — still valid).

## 4. Optimisations

### 4.1 Approval load — six gates, not thirteen

Add `auto_approve_on_pass` and `approval_threshold` to `StageConfig`. A stage advances without a
click when the verdict is `pass` **and** the score clears the threshold. Manual approval stays
only where a stage emits a verdict a human must own:

| Stage | Verdict owned |
|---|---|
| 01 | `framing_mode` — the prompt allows a reviewer to override |
| 02A | prohibited-practice check / risk tier |
| 07 | architecture review `pass \| conditional \| fail` |
| 07A | compliance gate `cleared \| conditional \| blocked` |
| 09 | `structural_reopen` `cleared \| blocked` |
| 13 | sponsor proposal sign-off |

### 4.2 Token cost — three levers, largest first

**Lever 1 — `depends_on` (I3).** `runner.py:133` passes *every* prior artifact to every stage.
The prompts already declare their prerequisites, so the dependency graph is free. Absolute
reduction, and better quality — less irrelevant context to be distracted by.

**Lever 2 — reorder the user message for prefix caching.** `composer.py:103` builds:

```
[stage_body] [use_case] [evidence] [prior_artifacts]
```

`stage_body` is the only part that changes across a stage's generate → validate → repair →
re-validate calls, yet it sits first, so nothing behind it caches. Reorder to:

```
[use_case] [evidence] [prior_artifacts] [stage_body]
```

The whole stable block becomes a cacheable prefix across all 3–4 calls of a stage. Cached input
is 50–90% cheaper *(Day 10)*, and instruction-last tends to help on long contexts. Sort
`prior_artifacts` by stage order so the prefix stays byte-stable. ~5 lines, but behaviour
changes — needs a comparison run.

**Lever 3 — model tiering.** `model:` on `StageConfig`. Strong validator on the six judgment
gates; cheaper tier on the seven structural stages. I1 already removes validator calls entirely
on structural failures.

**Do not pre-tune.** Ship levers 1 and 2, measure in the slice and again after wiring, then set
the model map from telemetry.

### 4.3 Artifact size — seams marked, do not pre-split

Prompt 08 declares eleven output files, Prompt 05 seven-plus. A validator judging a
fifteen-section document scores less sharply than one judging a focused document. Watch for
vague rubric comments; if they appear, splitting is a `pipeline.yaml` edit — `08` → contracts +
closure, `05` → specs + registers.

## 5. Phases

Sequenced around a **vertical slice**: one new stage proven end to end before 13 prompts and 13
validators are authored. This surfaces the three biggest unknowns — rubric quality at scale,
run cost and latency, section enforcement against real model output — in week one instead of at
the end.

### Phase 1 — Contracts *(unblocked)*

- **I2 — validator contract for declared uncertainty.** *(hard prerequisite)* The chain runs on
  `hypothesis`, `provisional`, `Unknown`, `TBD`, `spec_ambiguities`.
  `Prompts/_shared/validator_system.md` has no rule rewarding any of it and will score honest
  declarations as incomplete, pressuring the model toward fabrication. Add: a gap written as
  `UNKNOWN — <what> · owner: <role> · resolves by: <trigger>` is a **correct** answer and must
  not be penalised on completeness; an unmarked unsupported claim is `critical`.
- **I1 — enforce `required_sections` deterministically.** `models.py:36` declares the field;
  nothing reads it. Parse H2s between generate and validate; a miss routes straight to repair
  without spending a validator call. Variable-cardinality outputs (`ADR-001…`, `FR-001…`) become
  repeated H3s under a fixed H2 — only fixed sections are checkable.
- **`house_style.md`** — canonical `## Lean / DMAIC lens` heading and `UNKNOWN` / `Unknown
  baseline` forms.

**Done when:** `uv run pytest` green; a stage missing a declared section fails before the
validator runs; a `hypothesis`-mode artifact scores no worse than a `decision-ready` one of
equal quality.

### Phase 2 — Vertical slice *(the de-risk, and the demo)*

Wrap **02A `risk_classification`** only, author its validator, and insert it at order 3 of the
**existing five-stage pipeline**. Six stages. Run end to end on a real use case.

This exercises the entire mechanism on one stage: front-matter, `required_sections`, validator
rubric, `STAGE_LABELS`, artifact rendering, approval gate, repair loop.

**Done when:** a real use case produces a tiered EU AI Act classification with Annex III
reasoning, binding compliance dates, and declared `UNKNOWN` gaps — and per-stage token spend and
wall-clock are recorded.

**Also the showcase.** Feed in a use-case document, get back a compliance classification the
pack could not previously produce. See §6.

### Phase 3 — Runner *(informed by the slice)*

I3 `depends_on` · 4.1 `auto_approve_on_pass` · 4.2 composer reorder · 4.3 `model:` field.

**Done when:** a stage receives only its declared prerequisites; a passing structural stage
advances without a click; the cacheable prefix is verified byte-stable across a stage's calls.

### Phase 4 — Bulk migration *(blocked on user's files + §3 rework)*

Wrap the remaining twelve prompts with front-matter, convert each `Output` list into
`required_sections`, swap `case-study/*.md` conventions for `{{ use_case }}` / `{{ evidence }}`
per `docs/PROMPT-LIBRARY.md`, apply the §3 rework, and author twelve validators from Exit
criteria and Constraints.

**Done when:** `create_app()` loads the full library; `validate_pipeline_bindings` passes.

### Phase 5 — Wire the pipeline

`config/pipeline.yaml` with thirteen stages, `order`, `depends_on`, filenames, approval policy;
thirteen `STAGE_LABELS`. Artifact filenames renumber once, here — two test assertions pin names
(`tests/test_api.py:102`, `tests/test_prompt_registry.py:162`). Historical runs under `runs/`
are keyed by stage-id directory, not filename, so they are unaffected.

**Caveat:** drain or fail in-flight `awaiting_approval` runs before deploying.

**Done when:** a real use case completes all thirteen stages; the bundle holds thirteen
artifacts; the model map is set from measured spend.

### Phase 6 — Gates

- **I4 — backward loop (`revise_stage`).** Prompts 07, 07A and 09 emit gates that send work
  *backwards*; the pipeline is forward-only and `regenerate` loops within a stage only
  (`api/schemas.py:91`). Touches `state.py`, `runner.py`, `api/routes/runs.py`, `schemas.py`,
  `StageRail.tsx`.
- **I5 — gate extraction.** Lift `framing_mode`, `artifact_status`, `architecture_review`,
  `structural_reopen`, `compliance_gate` into run state and inject as Jinja variables
  (`registry.py:126` already supports `jinja_context`) so gates are enforced, not re-derived
  from prose.

**Done when:** a Prompt 09 `structural_reopen: blocked` verdict actually returns the run to
stage 06.

## 6. Showcase

The Phase 2 slice is the demo. A plan is not — *"short cycles create proof; ten-day shipping
loops beat months of AI theater"* (Day 14).

1. **A real run**, screen or recording, not slides.
2. **The generated compliance artifact** — the moment. A raw use-case document in, an EU AI Act
   tier with Annex III reasoning and binding dates out.
3. **One before/after number** — manual FDE hours vs pipeline minutes. Every Day 14 value slide
   is shaped this way.
4. **The DMAIC spine as the through-line** — the programme's own mental model from Day 18.
5. **The declared gaps, out loud.** Day 21: the blank *"bought more credibility than any of the
   filled boxes."* A pipeline that states what it does not know demos stronger than one that
   fills every field.

## 7. Deliberately excluded

| Candidate | Source | Why not |
|---|---|---|
| Prompt 10 — implementation tasks | v2 library | The coding-agent handoff. Cheap to add later (mechanical derivation from 08's contracts) if the pack ever needs to be agent-executable. |
| Prompt 12 — assurance | v2 library | Audits a running system. With no build, every material area returns `inconclusive (data scarcity)`. |
| Data-profiling gate — exists / usable / governed / missing | Day 20, 21 | Prompt 01's evidence register and sufficiency scores partly cover it. |
| Estimation & spike artifact — T-shirt sizing, uncertainty cone, NOT list | Day 21 | Absent from the chain, but an engagement artifact rather than a spec one. |
| PPTX export of the proposal | Day 14 | `python-pptx` is already a dependency but only parses today. Post-migration polish. |

## 8. Open items

1. **Prompt 13 rework** (§3) — strip build and assurance dependencies, relabel
   `specified | assumed | unknown`. Blocks Phase 4. *Your prompt — confirm whether I write it.*
2. **Prompt files on disk** — the uploaded copies show encoding corruption (`â€"` for `—`,
   `â€œ` for `"`). Check the sources; if corrupted, repair before wrapping or the mojibake
   reaches the model and lands in every artifact.
3. **Validators** — confirm they are derived from Exit criteria and Constraints rather than
   supplied.

Phases 1 and 2 depend on none of these. Phase 2 needs only 02A, which is already written.
