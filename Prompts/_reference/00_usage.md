# Prompt Library Usage

Run these prompts sequentially with the target repository available to the selected coding assistant. The library takes a decision problem from raw evidence through discovery, framing, domain modeling, architecture, decision records, build, assurance and a final proposal.

For every prompt:

- inspect evidence before making claims;
- cite filenames and record identifiers;
- separate facts, derivations, assumptions and open questions;
- respect the authority and accountability boundaries defined for the domain;
- do not invent missing rules, regulations or data;
- do not treat a prototype as a certified operational system;
- write outputs to the corresponding participant-output directory.

## How to adapt this library to your domain

These prompts are domain-agnostic. Before running them, substitute the placeholders below with the specifics of your case:

- `{DOMAIN}` — the business domain the decision work lives in.
- `{SYSTEM}` — the advisory application being scoped.
- `{DECISION_PROBLEM}` — the bounded decision or engineering question.
- `{ROLES}` / `{AUTHORITY_MATRIX}` — the accountable human roles and who may decide what.
- `{SOURCE_SYSTEMS}` / `{DATA_DICTIONARY}` — where evidence comes from and what each field means.
- `{PROHIBITED_ACTIONS}` — actions the system must never take (the safety/authority boundary).
- `{PRIORITY_RULE}` — which concerns may never be overridden by others (e.g. safety over commercial urgency).

Keep the same file names across the library so artifacts trace cleanly from one stage to the next.
