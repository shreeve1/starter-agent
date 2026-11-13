# Rules

Read at session start. Load every Always row now. Before each task, load every row whose When fits.

- One lead per task: empty, skill `name` or procedure `memory/workflows/<topic>/<slug>.md`. Also load adds supporting content, never an independent execution sequence. A matching `type: workflow` note is loaded as reference; only a matching `type: procedure` file is selected as Lead and gated with `gate.py procedures`.
- Specific owner-approved procedures take precedence over general skills. The more specific When wins; unresolved equally specific leads require asking the owner, not merging steps. Client exceptions apply only to their named client.
- Stop before any procedure step: if equally specific leads remain, ask which applies, even when their steps are identical. After selecting a lead, check readiness with `gate.py procedures memory/workflows/<topic>/<slug>.md` or compare the full Procedure File template manually without Python. Missing risk, Prerequisites, Verify or other required sections blocks execution; approved and verified are required for promoted procedures, and a draft needs its `### Gaps` section. Report gaps and wait for owner-assisted repair.
- Rows point; they hold no guidance. Content lives in the files they name.
- New rule: add a row (personal-memory "Rules"). `gate.py audit` fails a row naming a missing skill or file, and a preference file no row reaches.

| When | Lead | Also load | Note |
|---|---|---|---|
| Always | | `tasks/index.md` | Optional; skip absence without creating files. |
| Create, look up, continue, review, complete or archive a saved task | | skill `personal-memory` | Supporting bookkeeping; actual work keeps its lead. |
| Shorthand name of a host, service, person or system | | `memory/glossary.md` | |
| A word that sounds like a defined term | | `CONTEXT.md` | Delete this row if the project has no `CONTEXT.md`. |
| Work on one tracked thing | | `memory/clients/_hubs/<short>.md` | Template: rename to the project's word and folder when Client Memory is set up, otherwise delete. |
| The owner starts defining a procedure ("let's define a procedure for …") | skill `personal-memory` | `memory/TEMPLATES.md`, `memory/workflows/index.md` | Steps: personal-memory reference.md "Procedures". |
| A task a saved procedure or workflow covers | | `memory/workflows/index.md` | Load a matching `type: workflow` note as reference; select only a matching `type: procedure` file as Lead and gate it with `gate.py procedures`. When the index is split, open the topic page it points to. Procedures in personal-memory reference.md "Procedures" apply. |
| A procedure run ends, or the owner asks how a procedure is doing | skill `personal-memory` | | Run review: reference.md "Procedures". |
| Saving, pruning or checking memory | skill `personal-memory` | | |
