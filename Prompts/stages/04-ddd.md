---
id: stage.domain_model
version: 2.0.0
stage: domain_model
model_role: generator
inputs: [use_case, evidence, prior_artifacts]
output_format: markdown
required_sections:
  - Artifact Status and Domain Framing
  - Ubiquitous Language and Bounded Contexts
  - Domain Events and Model
  - Rules, AI and HITL Boundaries
  - Retrieval and Evidence Design
  - Minimum Governed Workflow and Pilot Notes
  - Lean / DMAIC Lens
---
# Prompt 04 — Domain-Driven Design for Gen AI

Model the **business** first, then define where hard rules, AI reasoning, retrieval, agents, and
human-in-the-loop review each fit — before any feature flow or architecture diagram is drawn. The
theme: from domain meaning to governed Gen AI delivery.

If the narrative class carried forward from SCQA is `hypothesis`, or if critical ubiquitous
language or source-of-truth questions remain open, mark every output in this stage **provisional**
— prefer rules and human review over autonomous AI wherever the domain is uncertain, and name what
evidence would need to arrive before the model could be trusted as stable.

## Artifact Status and Domain Framing

State the **artifact status** — `stable` | `provisional` — first; use `provisional` when the
narrative class is `hypothesis` or when a critical ubiquitous-language or source-of-truth question
is still open. Then restate the SCQA/PRD ask in domain terms, respecting the PRD's scope, and
identify the domain and its subdomains — core, supporting, and generic.

## Ubiquitous Language and Bounded Contexts

Build the shared vocabulary: list ambiguous or overloaded terms and how each is resolved, or mark
it "unresolved — provisional." Define bounded contexts, each with a business owner and the
decisions that owner is accountable for (owners may be `TBD — owner: <role>` if stakeholders are
scarce — flag it, do not invent an owner). Then draw the context map as a fenced ```plantuml```
diagram per house style — one box per bounded context, one labelled arrow per relationship
(upstream/downstream, conformist, anti-corruption layer, or shared kernel, whichever actually
applies). A prose list of relationships is not a substitute for the diagram; produce both. Name
the anti-corruption requirements that guard against misleading source-specific language leaking
across a boundary.

## Domain Events and Model

The domain events this system must be aware of (event storming or equivalent), and the entities,
value objects, aggregates, and invariants that carry the business rules that must always hold.

## Rules, AI and HITL Boundaries

Separate deterministic business logic from probabilistic AI output: state plainly what AI must
never decide alone. Then design agent responsibilities where agents apply — tasks per agent,
authority limits, and stop conditions — and define human-in-the-loop and decision ownership: when
a human intervenes, and who owns that decision.

## Retrieval and Evidence Design

If retrieval applies: what is retrieved, from which artefacts or sources, and what is deliberately
out of retrieval scope — designed from this stage's own domain artefacts, not from whatever data
happens to be lying around. Design the evidence and audit trail — what must be recorded for
transparency and later review — and define evaluation in this domain's own vocabulary: domain-true
success and failure cases and the metrics that would distinguish them (evaluation intent only;
building the harness is later work).

## Minimum Governed Workflow and Pilot Notes

The smallest controlled flow that delivers the outcome framed in SCQA/PRD — this is the shape the
architecture stage will realise, so keep it to what is actually governed, not what would be
impressive. Then: what would need to be learned before this domain model could be trusted at
scale (emphasise this if the artifact status is `provisional`), and, from a domain perspective
only, the ownership and boundary risks a later handover would need to resolve — not a full
architecture view, just what a domain owner would need to know. Link back to any item in
Discovery's evidence acquisition backlog that would move this model from provisional to stable.

## Lean / DMAIC Lens

This stage's focus is **Analyze** (where defects and rework originate in the domain) and designing
to avoid waste before it is built in. Record: which invariants or rules remove **Defects**
(hallucinations, bad decisions) versus leaving them to the model's judgement; where human-in-the-
loop prevents human-review waste (reviewing everything) while still catching genuinely high-risk
cases; the retrieval and agent boundary risks of token, retrieval, or context waste if left
unbounded; and which domain ambiguities would cause extra processing or motion if left unresolved
into the next stage.

Do not produce a feature-flow document, a C4 diagram, or a decision record here — raise them only
as brief open questions for the stages that own them. Do not choose a vendor or model unless the
evidence forces a hard constraint, in which case flag it as a decision candidate rather than
settling it. Do not treat a dataset name or an API shape as the domain model, and do not present a
`provisional` model as production-ready domain truth.

Use exactly these `##` section headings, in this order: Artifact Status and Domain Framing,
Ubiquitous Language and Bounded Contexts, Domain Events and Model, Rules, AI and HITL Boundaries,
Retrieval and Evidence Design, Minimum Governed Workflow and Pilot Notes, Lean / DMAIC Lens.
