# Personal Memory Reference

Rare operations for the `personal-memory` skill: recovering missing scaffold and linting memory health. `SKILL.md` covers everyday capture and reads; open this file only for one of these two. `<skills>` is defined in `SKILL.md`.

## Setup Workflow

For setup and migration, use the `memory-setup` skill.
Copy missing scaffold from `<skills>/personal-memory/scaffold/`.

## Recovery Workflow

Scaffold or personal files may be missing in a fresh copy of a
project. Before writing any promoted memory in a run, ensure the scaffold
exists first, then recover the personal files:

- If `memory/README.md` or `memory/TEMPLATES.md` is missing, recreate it — it is
  scaffold, not personal state. Restore `README.md` as the memory
  contract and `TEMPLATES.md` as the canonical templates, copying it from
  `<skills>/personal-memory/scaffold/`.
- If `memory/index.md` is missing, recreate it from the `TEMPLATES.md` index template before writing promoted memory.
- `memory/log.md` is retired. Never recreate it.
- If `TEMPLATES.md` is itself unavailable, do not block: fall back to the
  templates embedded in this skill and the format docs, and recreate
  `TEMPLATES.md` from them.
- Missing personal files are normal, not an error.

## Lint Workflow

Use when asked to review memory health or before broad cleanup.

Run the deterministic index audit first:

`python3 <skills>/personal-memory/gate.py --memory memory audit`

Without Python, use the hand checks in `SKILL.md` Capture Workflow step 6, then review the items below. Say that the audit was not run.

It reports promoted files missing from `memory/index.md`, index entries pointing to files that no longer exist, topic-folder problems (a promoted file directly in `workflows/`/`decisions/`, a topic folder not in `memory/schema.json`, a sub-index missing a file or drifted from `indexes.py`), and Client Memory problems (missing frontmatter keys, unknown subject, subject/client not matching the folders, note not on its hub, hub out of date, hub without an `index.md` row), and exits non-zero when anything needs fixing. It also prints `crowded` warnings (a memory folder holding more than 15 `.md` files directly) but does not fail on them. Fix hub problems by running `hubs.py`; fix sub-index drift by running `indexes.py`. `memory/candidates/` is not audited. For `gate.py audit` to recognize an index entry, the row must carry the file path either backticked (`` `memory/decisions/<topic>/decision-x.md` ``) or as a markdown link (`[title](memory/decisions/<topic>/decision-x.md)`).

Then also check for:

- Index rows pointing to missing files.
- Promoted files missing from `memory/index.md`.
- Empty promoted topic files.
- Conflicting active promoted rules.
- Cross-links pointing to memory files that do not exist (report only — broken links are tolerated, not auto-removed).

Report findings before making broad changes. Safe deterministic fixes include removing stale rows and adding missing index rows for existing files.

Note on `gate.py`: `audit` checks `memory/index.md` against the promoted files and Client Memory on disk, checks `memory/rules.md`, and prints lean-memory warnings (size, summary length, history lines, superseded files). `stale` lists notes not updated or verified in 90 days. It checks structure only; it does not check whether a memory item is true (see the grounding rule in Capture Workflow).
