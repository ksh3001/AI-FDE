# Single Prompt — Domain-Driven Design ({DOMAIN})

> Consolidates Stages 1–7 of the DDD-Lab step pipeline (business framing → domain/subdomain map →
> ubiquitous language → bounded contexts → context map → event storming → domain model & invariants)
> into one prompt, optimized for the **{DECISION_PROBLEM}** case.
> Run it after the SCQA decision narrative exists. Paste the sections below into your model, attaching
> the case-study and data-reference files it names.

---

You are the context-engineering assistant for an **AI Forward Deployed Engineering × Domain-Driven Design workshop**.

## Inputs to use

Read only these attached inputs and reason strictly from them:

1. `case-study/00_executive_case.md` — the `{DECISION_PROBLEM}` case.
2. `case-study/02_stakeholders_and_conflicting_needs.md` — stakeholders and their conflicting incentives.
3. `case-study/03_constraints_authority_and_non_negotiables.md` — authority limits and evidence discipline.
4. `{AUTHORITY_MATRIX}` — who is authorized to decide what.
5. `{SOURCE_SYSTEMS}` and `{DATA_DICTIONARY}` — source systems and field meanings.
6. `participant-outputs/02-scqa/scqa_decision_narrative.md` — the agreed decision problem (if present).

## Mission

In a single pass, derive the **complete business-domain DDD model** for the `{DECISION_PROBLEM}` and
produce the artifacts listed under **Required outputs**. Move deliberately through the seven reasoning stages
below, but deliver them as one coherent, internally consistent set of documents.

## Hard rules (non-negotiable)

1. Use only the attached inputs. Do **not** invent entities, transactions, locations, telemetry, incidents, or regulations.
2. This is a **business-domain** DDD artifact. Do **not** design architecture, services, APIs, databases, GenAI,
   RAG, MCP, agents, or any technical implementation. That belongs to later C4/ADR stages.
3. The application being scoped is **advisory only**. The model must never imply the system can perform, control,
   execute or authorize any of the `{PROHIBITED_ACTIONS}`, declare an entity fit/unfit or compliant/non-compliant,
   approve or reject transactions, or write to any operational or control system.
4. **Human authority stays visible.** Every decision in the model must name an accountable human role drawn from
   the `{AUTHORITY_MATRIX}`. The model must not allow any of these to be bypassed or auto-executed.
5. **Evidence discipline is a first-class domain concern.** Preserve the distinction between source timestamp,
   receipt timestamp and timezone; preserve original source identifiers; keep conflicting records visible; never
   treat missing information as normal; show formula, source and assumptions for any derived value; resolve
   entity / process / event identity **without destroying provenance**.
6. **`{PRIORITY_RULE}`** must hold in any rule, invariant, or relationship you write (e.g. safety, environmental,
   security, compliance or statutory authority may never be overruled by commercial urgency).
7. Do **not** organize the domain around technical layers, source-system names, or dataset/table names. The domain
   is the *decision work being performed*, not the systems that store the data.
8. Do **not** resolve the operational exceptions in the case. Represent them as domain gaps, exception states, and
   invariants — never as solved problems.
9. Do not assume the most commercially visible problem is the most important one.

## Reasoning stages to work through (deliver as one output set)

**Stage 1 — Business problem framing.** Restate the decision problem in business terms; decompose it into risk
classes relevant to `{DOMAIN}` (e.g. safety, environmental, security/cyber, technical condition, people & compliance,
resource/quality, commercial/contractual, evidence & audit). Identify affected roles and desired outcomes. No
technology language.

**Stage 2 — Domain & subdomain map.** Name the main business domain and classify subdomains as **core**
(central to the cross-functional prioritization and case-level investigation), **supporting**, and
**generic/reusable**. For each: purpose, key responsibilities, risk if weak. Map known gaps to subdomains and note
natural owners without finalizing accountability.

**Stage 3 — Ubiquitous language.** Define the shared language **as used in this case** (not a universal domain
dictionary). Capture core terms, subdomain terms, status/exception/approval terms, ambiguous terms interpreted
differently by different roles/source systems, and terms that must not be used loosely because they imply safety,
authority, release, fitness, or completion.

**Stage 4 — Bounded contexts.** Split the domain into bounded contexts, each with its own language, ownership,
statuses/decisions, dependencies, gaps, and audit needs. Do **not** create one giant catch-all "operations" context.
Give each a full canvas (fields listed in the output spec). Derive the contexts from the case; merge/split only with
a clear business reason. Ensure at least a dedicated **Evidence & Provenance** context and a dedicated **Decision
Authority & Accountability** context exist.

**Stage 5 — Context map.** Show upstream/downstream relationships, and use DDD relationship language where it fits
(partnership, shared kernel, published language, anti-corruption layer). Make ownership, translation/handoff risk,
and audit requirement visible for each relationship. Identify shared kernel terms, published handoff vocabulary,
partnerships, and anti-corruption boundaries where a source system's or one context's language could distort
another's meaning. **Defend the map**: for each relationship give a one-line rationale (why this relationship type
and direction, and why this boundary rather than merging or splitting the contexts), and note the safety/authority
or translation risk that the boundary is protecting against. Also emit a **PlantUML** context diagram.

**Stage 6 — Event storming.** Produce a business-domain event board: domain events (things that happened),
triggering commands/activities, primary human actor, bounded context, governing policy/rule, evidence source,
failure/exception condition, and audit need. Keep exceptions unresolved.

**Stage 7 — Domain model & invariant register.** Classify candidate objects into entities, value objects,
aggregate roots, policies/rules, evidence/audit artifacts, external references. Give entity / value-object /
aggregate registers, aggregate detail canvases, an **invariant register** (invariant ID, statement,
aggregate/context, source rule or case fact, human owner, failure risk, audit evidence required), and a separate
**policy register** (policy ID, policy statement / "when X then Y must happen", triggering domain event,
bounded context, accountable human owner, source rule or case fact, audit evidence required). Show unresolved
exceptions as domain state and preserve human decision ownership in the model.

## Required outputs

Write these files under `participant-outputs/03-ddd/`:

1. **`domain_landscape.md`** — Stages 1–3: business problem framing, domain & subdomain map, and the narrative
   parts of the ubiquitous language (principles, ambiguous terms, terms that must not be used loosely), plus the
   event-storming board (Stage 6) and the domain-model, invariant register, and policy register (Stage 7).
2. **`ubiquitous_language.csv`** — one row per term with columns:
   `term, definition_in_this_case, bounded_context, owner_role, valid_context, ambiguity_risk, must_not_be_used_loosely`.
3. **`bounded_context_canvases.md`** — one canvas per bounded context with:
   context name · business purpose · primary human participants · owned language · owned information/statuses ·
   decisions/statuses owned · decisions **not** owned · upstream inputs · downstream outputs · policies/rules it
   must respect · anti-corruption/translation needs · known gaps touching it · audit/evidence needs ·
   safety/authority risk if the boundary is misunderstood.
4. **`context_map.puml`** — PlantUML source for the context map, showing contexts, relationship types
   (upstream/downstream, partnership, shared kernel, published language, ACL), and safety-critical handoffs.
   Keep it renderable to `context_map.svg` / `context_map.png`.

## Quality gate (self-check before finishing)

- Every bounded context has distinct language and a named human owner; no context silently owns another's decision.
- Every invariant and policy traces to a case fact or stated rule and names the human owner of the decision it guards.
- Every context-map relationship carries a one-line rationale (defence) and the risk its boundary protects against.
- No rule lets `{PRIORITY_RULE}` be violated.
- Provenance (source id, source vs. receipt timestamp, timezone, conflicts, missing-data) is modeled explicitly.
- No architecture, source-system, or dataset names used as domain concepts.
- Every operational exception in the case appears as a gap/exception state or invariant — none resolved.
- `ubiquitous_language.csv` and `context_map.puml` are consistent with the canvases and the domain landscape.

End the output with: **"{DOMAIN} DDD complete."**

Write outputs under `participant-outputs/03-ddd/`.
