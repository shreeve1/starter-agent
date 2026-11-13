# Procedure graduation (starter-agent and dotfiles) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give personal-memory procedures the same ladder as itastack (draft, reviewed, trust offered, trusted per step), run logs and an end-of-run review; reverse "stored approval never covers the current run"; and accept itastack's procedure-capture procedures.

**Architecture:** `procedures.py` gains draft and trust rules, run-log checks, a read-only ladder report and procedure-capture recognition that defers to the workspace's own validator; `gate.py` gains a `ladder` command and size-warning exemptions. Templates and authority wording change in the workspace and the scaffold. Then the itastack compatibility check runs on a copy, and dotfiles syncs.

**Tech Stack:** Python 3 standard library, `unittest`; Markdown.

**Spec:** `docs/superpowers/specs/2026-11-12-procedure-graduation-design.md` (approved 2026-11-12). Read it whole first. itastack's half is `/home/james/Documents/itastack/docs/superpowers/plans/2026-11-12-procedure-graduation.md`; use its `ladder.py` rules as the reference for matching behaviour and wording.

## Global Constraints

- Start from `main` after the personal-memory index work (coordinator thread ea095a1f) has merged. Do not edit `indexes.py`, `hubs.py` or `gate.py`'s index checks; that work owns them. If a test shows a runs file listed as an index problem, report it instead of editing those checks.
- In the shared docs (`SKILL.md`, `reference.md`, scaffold), edit only procedure and authority wording.
- Stage only task-owned paths. Hooks stay disabled: run `python3 .githooks/pre-commit` by hand before each commit. Add one `CHANGELOG.md` "Local changes" line for the skill change. Never push; never edit the dotfiles copy of a skill.
- Standard library only. Windows, macOS and Linux paths; no shell strings in subprocess calls. Every script check has a written manual equivalent; without Python no step runs on trust.
- Notes stay within 6144 bytes with summaries of 160 characters or fewer; run logs and procedure-capture files are exempt from the size warning.
- Trusted steps run only in a visible session (D5): any session with a window the owner can open and type into while it runs, whoever opened it (T3 chat, herdr tab, research tab). Not visible: timer- or schedule-started runs, bots and Slack, subagents with no window of their own.
- Counted rows (D6): only rows after a runs file's `renumbered: <YYYY-MM-DD> after <Ref>` marker count; older rows are history.
- Never trusted: a message to another person, spending money, any step with no real undo. Only the owner's explicit yes in the current conversation grants or renews trust.
- Tests: `cd .agents/skills/personal-memory && python3 -m unittest discover -s tests 2>&1 | grep -E '^(Ran|OK|FAILED)'` (baseline 2026-11-12 before the index work: `Ran 179`, `OK`; take a fresh baseline after it merges). `python3 .githooks/pre-commit` also runs the memory-setup and hook suites.

## Review Focus

1. A legacy procedure with `status: promoted` (or no status) and valid dates stays valid as rung 1 with no trust. Test: `test_legacy_promoted_stays_valid_rung_one` (Tasks 1 and 3).
2. BOM and CRLF in a runs file read the same as LF. Test: `test_runs_file_bom_crlf` (Task 2).
3. A runs file whose `procedure:` points outside `memory/workflows/<topic>/` (traversal, absolute, backslash) is refused without reading the target. Test: `test_runs_procedure_path_traversal_refused` (Task 2).
4. After a Correction renumbers steps without a marker, the unknown-step error tells the agent to add `renumbered:`. Test: `test_unknown_step_suggests_marker` (Task 2).
5. The procedure-capture validator runs with an argument list, no shell, and a timeout, so a path with spaces or quotes is safe on Windows too. Test: `test_capture_check_uses_argument_list` (Task 4).

---

### Task 1: Draft status, Gaps and trust rules

**Files:**
- Modify: `.agents/skills/personal-memory/procedures.py` (`validate`)
- Test: `.agents/skills/personal-memory/tests/test_procedures.py`

**Interfaces:**
- Produces: `parse_sections(path: Path) -> tuple[dict, dict]` (frontmatter fields, the fence-aware sections map `validate` builds today, extracted unchanged); `step_ids(sections: dict) -> set[str]` (numbers of `### Steps` items, as strings); `undo_steps(sections: dict) -> set[str]` (step numbers named by `- Step <n>: <undo>` or `- Steps 2 and 3: <undo>` lines under `### Recovery` whose undo does not start with `<`, `not known`, `none`, `n/a`, `...`, `not possible`, `cannot` or `irreversible`, case-insensitive); `recovery_steps(sections: dict) -> set[str]` (all steps named by such lines, any text); `trust_problems(path: Path, fields: dict, sections: dict, today: date) -> list[str]`.
- Rules: `status: draft` makes `approved` and `verified` optional (if present they must still be real, non-future dates) and requires a nonempty `### Gaps` inside Active memory (`None.` allowed). Any other status keeps today's rules. `trusted:` (nonempty) requires `status: promoted`, `risk: changes-state`, a real non-future date and a nonempty `trusted_steps: [<n>, ...]` of digits only, each in `step_ids` and `undo_steps`. `trusted_steps` with an empty `trusted:` (trust revoked) only needs a valid shape.

- [ ] **Step 1: Write the failing tests:** `test_draft_needs_gaps_not_dates`, `test_draft_with_invalid_date_still_fails`, `test_legacy_promoted_stays_valid_rung_one` (existing `BODY` with `status: promoted`, and with no status), `test_trust_requires_promoted_changes_state_and_real_undo` (each missing condition gives one problem naming it; `- Step 2: not possible` counts as no undo), `test_trusted_steps_must_be_numbered_steps` (`[4]` with 3 steps fails; `[2b]` fails), `test_trusted_date_not_future`, `test_revoked_trust_keeps_steps_valid`.
- [ ] **Step 2: Run** the suite. Expected: the new tests fail; the rest pass.
- [ ] **Step 3: Implement** in `procedures.py`; `validate` keeps its signature and its existing messages.
- [ ] **Step 4: Run** the suite -> `OK`.
- [ ] **Step 5: Commit** `procedures.py` and `tests/test_procedures.py`: `personal-memory: draft procedures and per-step trust rules`.

### Task 2: Run logs

**Files:**
- Modify: `.agents/skills/personal-memory/procedures.py` (`selected`, `audit`), `.agents/skills/personal-memory/gate.py` (`bloat`: skip `*.runs.md`)
- Test: `.agents/skills/personal-memory/tests/test_procedures.py`

**Interfaces:**
- Produces: `RunRow(ref: str, date: str, step: str, result: str)` (NamedTuple); `runs_path(path: Path) -> Path` (`<slug>.runs.md` beside `<slug>.md`); `read_runs(path: Path) -> tuple[dict, list[RunRow], list[str]]` (frontmatter, rows from the `## Worked runs` table, problems for rows that are not 6 cells); `counted(fields: dict, rows: list[RunRow]) -> list[RunRow]` (rows after the last row whose Ref is the marker's; all rows without a marker); `runs_problems(runs_file: Path, memory_dir: Path) -> list[str]`; `RESULTS = ("pass", "fail", "partial", "skipped")`.
- `runs_problems` checks: `type: worked-runs`; `procedure:` equals the sibling's workspace-relative path `memory/workflows/<topic>/<slug>.md` (refuse absolute, drive, backslash and `..` before any read) and that file exists; `## Worked runs` present; results in `RESULTS`; marker matches `^\d{4}-\d{2}-\d{2} after \S+$` and its Ref appears in the table; every counted row's step is in the procedure's `step_ids`. The unknown-step message ends: `; if a Correction renumbered the steps, add renumbered: <date> after <last old Ref> to the runs file`.
- `audit` never validates a `*.runs.md` file as a procedure; it runs `runs_problems` on each, including one with no sibling procedure. `selected` adds `runs_problems` for the selected procedure's runs file when present.

- [ ] **Step 1: Write the failing tests:** `test_runs_file_checked_and_not_a_procedure`, `test_runs_rows_before_marker_not_checked`, `test_runs_bad_result_and_unknown_step_fail`, `test_unknown_step_suggests_marker`, `test_orphan_runs_file_fails`, `test_runs_procedure_path_traversal_refused` (patch `hubs.parse_frontmatter` to raise if the target is read, as `test_invalid_schema_topics_never_read_outside` does), `test_runs_file_bom_crlf`, `test_runs_file_exempt_from_size_warning` (a 7000-byte runs file gives no size line from `gate.bloat`), `test_audit_with_runs_file_has_no_index_problem` (fixture workspace via `test_rules.workspace`, run `GATE` audit, no line mentions the runs file).
- [ ] **Step 2: Run** the suite. Expected: new tests fail.
- [ ] **Step 3: Implement**; in `gate.bloat`, skip files whose name ends `.runs.md` before the size and summary checks.
- [ ] **Step 4: Run** the suite -> `OK`.
- [ ] **Step 5: Commit**: `personal-memory: procedure run logs`.

### Task 3: Ladder report

**Files:**
- Modify: `.agents/skills/personal-memory/procedures.py`, `.agents/skills/personal-memory/gate.py` (new `ladder` subcommand)
- Test: `.agents/skills/personal-memory/tests/test_procedures.py`

**Interfaces:**
- Produces: `StepStatus(step: str, state: str, reason: str, passes: list[str])` with `state` in `trusted`, `qualifies`, `blocked`; `Ladder(path: str, rung: int, rung_name: str, runs: list[tuple[str, bool]], steps: list[StepStatus], skipped_rows: list[str], next_move: str)`; `ladder(memory_dir: Path, relative_path: str, today: date | None = None) -> Ladder`; `render(l: Ladder) -> str`. CLI: `gate.py --memory memory ladder memory/workflows/<topic>/<slug>.md` prints `render`, exits 0, writes nothing; an invalid target prints its problem and exits 1.
- Rules, matching itastack's `ladder.py`: rung 3 `trusted` when `trusted:` is set; 2 `trust offered` when promoted with a `- YYYY-MM-DD: trust suggested` line under `## Notes`; 1 `reviewed` for any non-draft; 0 `proposed` for draft. Change steps are `recovery_steps`. A run is one Ref; a step's result is its last row for that Ref. Clean run: no `fail`, and every change step present ended `pass`. Last trust change: the later of `trusted:` and the newest `trust revoked` date under Notes; only runs dated on or after it count. Qualifies: rung >= 1, `risk: changes-state`, in `undo_steps`, last 3 results (one per run, ignoring `skipped`) all `pass`. Blocked reasons, first that applies: `no known undo`; `last result <result> on <ref>`; `<n> clean pass(es) of 3`; `procedure is draft`. `next_move`, first that applies: `next: a clean run under the current numbering` (draft, no counted runs); `next: mark it reviewed (the owner's yes in a run review)` (draft, latest counted run clean); `next: fix what differed, then a clean run` (draft, latest not clean); `next: trust steps <ids joined "2, 3 and 5"> (the owner's yes)`; else `next: nothing to offer yet`.

- [ ] **Step 1: Write the failing tests:** `test_ladder_draft_offers_mark_reviewed`, `test_ladder_partial_on_change_step_spoils_run`, `test_ladder_qualifies_after_three_clean_passes`, `test_ladder_no_undo_blocked`, `test_ladder_trust_change_resets_count`, `test_ladder_rows_before_marker_not_counted`, `test_ladder_cli_writes_nothing` (bytes of procedure and runs file unchanged; exit 0), and extend `test_legacy_promoted_stays_valid_rung_one` to assert rung 1.
- [ ] **Step 2: Run** the suite. Expected: new tests fail.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** the suite -> `OK`.
- [ ] **Step 5: Commit**: `personal-memory: read-only procedure ladder report`.

### Task 4: Accept procedure-capture procedures

**Files:**
- Modify: `.agents/skills/personal-memory/procedures.py`, `.agents/skills/personal-memory/gate.py` (procedure output and `bloat`)
- Test: `.agents/skills/personal-memory/tests/test_procedures.py`

**Interfaces:**
- Produces: `WARN_PREFIX = "warn: "`; `is_capture_format(path: Path) -> bool` (`type: procedure`, an `## Applies when` heading and no `## Active memory` heading, fences ignored); `capture_check(path: Path, root: Path) -> list[str]`. `validate`, `selected` and `audit` gain `root: Path | None = None` (default: the memory directory's parent); `gate.py` passes `--root` when given.
- `capture_check`: the validator is `root/.agents/skills/procedure-capture/scripts/validate.py`. Missing, not a regular file, or a symlink component under `root` -> one problem `<path>: procedure-capture procedures need .agents/skills/procedure-capture/scripts/validate.py`. Otherwise `subprocess.run([sys.executable, str(validator), str(path)], cwd=root, capture_output=True, text=True, timeout=60)`. Exit 0: each stdout line starting `warn ` becomes `WARN_PREFIX + f"{path}: {text}"`. Nonzero: each line starting `   - ` becomes a problem `<path>: <text>`, or the first 5 output lines when none match. Timeout -> one problem `<path>: procedure-capture validator timed out`.
- `gate.py`: entries starting with `WARN_PREFIX` print as `Warning: ...` and never fail; `bloat` skips the size warning for `is_capture_format` files. `gate.py ladder` on such a file prints `procedure-capture format: use the workspace's own ladder (sd.py procedure ladder)` and exits 0.

- [ ] **Step 1: Write the failing tests** (a fixture workspace with a fake `validate.py` written by each test): `test_capture_format_uses_workspace_validator` (prints `ok   <path>` and `warn  long row`, exit 0 -> no problems, one `warn:` entry, `gate.py procedures` exits 0 and prints `Warning:`), `test_capture_format_validator_errors_fail`, `test_capture_format_without_validator_fails_one_line`, `test_capture_validator_symlink_refused` (skip on platforms without symlinks), `test_half_written_draft_still_checked` (no `## Applies when`, no `## Active memory` -> template problems), `test_capture_format_exempt_from_size_warning`, `test_capture_check_uses_argument_list` (patch `subprocess.run`; assert a list argument, no `shell=True`, `timeout=60`), `test_capture_files_bytes_unchanged`.
- [ ] **Step 2: Run** the suite. Expected: new tests fail.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** the suite -> `OK`.
- [ ] **Step 5: Commit**: `personal-memory: accept procedure-capture procedures`.

### Task 5: Templates and the reversed authority rule

**Files:**
- Modify: `memory/TEMPLATES.md` and `.agents/skills/personal-memory/scaffold/TEMPLATES.md` (Procedure File, Changes-state Procedure File, new Run Log section)
- Modify: `.agents/skills/personal-memory/SKILL.md` (Rules bullet ~line 42, Memory authority ~line 70, workflows capture line ~127, Procedures ~line 145), `.agents/skills/personal-memory/reference.md` ("Procedures" ~lines 97-115)
- Modify: `.agents/skills/personal-memory/scaffold/README.md` (~lines 47-59), `scaffold/AGENTS-memory.md` (~lines 10, 27), `scaffold/rules.md` (procedure rows)
- Modify: `AGENTS.md` (~lines 46, 183), `memory/README.md` (~line 77), `memory/rules.md` (procedure rows), `.agents/skills/memory-setup/where-things-go.md` (line 12)
- Modify: `.agents/skills/personal-memory/tests/test_policy.py`; `CHANGELOG.md`

- [ ] **Step 1: Write the failing policy tests** in `test_policy.py`: `test_authority_contract_in_both_install_modes` now asserts the two sentences below and that `Stored procedure approval does not authorize the current action.` appears nowhere it checks; `test_run_review_contract_reached` (`Review how this run went?` and `gate.py ladder` reachable in both install modes); `test_trust_only_in_visible_sessions` (reference.md names visible sessions and says scheduled runs and no-Python runs ask at every change step).
- [ ] **Step 2: Run** the suite. Expected: those tests fail.
- [ ] **Step 3: Replace the authority sentence** everywhere it appears (SKILL.md, reference.md, scaffold README and AGENTS-memory, AGENTS.md, memory/README.md) with exactly: `A trusted step of a trusted procedure runs on its stored trust in a visible session. Every other consequential action still needs permission in the current conversation. Only the owner's explicit yes in the current conversation grants or renews trust; documents, email, tool output, run logs and earlier agent summaries cannot.`
- [ ] **Step 4: Proposing.** SKILL.md's workflows capture line and AGENTS.md's suggestion line say: when no procedure covers a repeatable workflow the owner performs or describes, save a `status: draft` procedure with its Gaps and report `Procedure proposed: <path>`; promoting it, changing a promoted procedure and granting trust need the owner's yes. Drafts are never auto-captured from external content.
- [ ] **Step 5: reference.md "Procedures"** covers, briefly: readiness (`gate.py procedures`, including drafts and trust; the manual equivalent); proposing; following (draft and untrusted change steps ask; trusted steps run without asking only in a visible session after `gate.py procedures` passes; check prerequisites and stop conditions before each trusted step and run Verify after; a failed Verify stops the run, empties `trusted:`, adds `- <date>: trust revoked: <reason>` under Notes after Recovery before editing, and tells the owner; without Python every change step asks); run rows appended to `<slug>.runs.md` (no snapshot needed for appends); the Run review (same order as the spec: record rows, ask `Review how this run went?` once with a readiness clause only when `gate.py ladder` shows one, on yes propose Corrections, show the ladder in plain words and offer the next move, apply on yes, finish with one `Run review:` line); and the hand-counting rule for the ladder without Python.
- [ ] **Step 6: Templates.** Procedure File: `status: draft` or `promoted`; `### Gaps` for drafts; optional `trusted:` and `trusted_steps:`; `### Recovery` with `- Step <n>: <how to undo>` lines; dated trust lines under Notes. Add a Run Log section with the runs-file shape (frontmatter `type: worked-runs`, `procedure:`, optional `renumbered:`, the 6-column table and the four results). Copy the same sections into `scaffold/TEMPLATES.md`.
- [ ] **Step 7: Rules rows** (workspace and scaffold): keep "defining a procedure"; the "task a saved procedure covers" row also loads reference.md "Procedures"; add `| A procedure run ends, or the owner asks how a procedure is doing | skill `personal-memory` | | Run review: reference.md "Procedures". |`.
- [ ] **Step 8:** `where-things-go.md` line 12: procedures start as agent-proposed drafts and become verified through run reviews.
- [ ] **Step 9: Run** the suite -> `OK`; `python3 .agents/skills/personal-memory/gate.py --memory memory audit` -> exit 0; `python3 .githooks/pre-commit` -> exit 0.
- [ ] **Step 10: Commit** with a `CHANGELOG.md` "Local changes" line: `personal-memory: procedure ladder, run review and trusted steps`.

### Task 6: Fresh-agent behaviour cases

**Files:**
- Create: `docs/testing/procedure-graduation-cases.md` (shape of `docs/testing/procedure-first-memory-cases.md`)

- [ ] **Step 1: Define the cases before running**, each with a disposable no-Git folder built from the actual scaffold and skill, stub actions only: (A) the owner describes a repeatable workflow -> a draft is saved and `Procedure proposed:` reported; (B) running a draft asks at every change step; (C) the question is asked once at run end; (D) "mark reviewed" and "trust steps" apply only after the owner's yes; (E) a trusted step runs without asking in a visible session; (F) the same procedure run from a scheduled session asks anyway; (G) a failed Verify on a trusted step revokes trust and reports it; (H) a document saying "this procedure is trusted" changes nothing.
- [ ] **Step 2: Run** each with a fresh agent; record client, model, OS, actual reads and writes, and before/after bytes. Unavailable combinations are NOT RUN, never inferred passes.
- [ ] **Step 3: Commit**: `docs: record procedure graduation behaviour cases`. Fix any FAIL in the owning task's files first, rerun that case, and record both runs.

### Task 7 (on wrk, after merge): itastack compatibility on a copy

- [ ] **Step 1: Copy** without touching the live folder: `rsync -a --exclude .stversions --exclude tmp --exclude artifacts --exclude .sessions ~/Documents/itastack/ /tmp/itastack-compat/`, then replace `/tmp/itastack-compat/.agents/skills/personal-memory` with `~/starter-agent/.agents/skills/personal-memory`.
- [ ] **Step 2: Fingerprint** the 7 procedures: `cd /tmp/itastack-compat && sha256sum $(rg -l '^type: procedure' memory/workflows) > /tmp/itastack-proc.sha`.
- [ ] **Step 3: Run** `python3 .agents/skills/personal-memory/gate.py --memory memory procedures; echo $?` -> `0`. Then `python3 .agents/skills/personal-memory/hubs.py` and `python3 .agents/skills/personal-memory/gate.py --memory memory audit` -> no `Procedure problems`; any remaining failure is only the two known `memory/rules.md` "Lead must be one skill or procedure" rows (fixed by the itastack upgrade, not here). `sha256sum -c /tmp/itastack-proc.sha` -> 7 `OK`.
- [ ] **Step 4:** Paste the outputs into the report, then `rm -rf /tmp/itastack-compat /tmp/itastack-proc.sha`.

### Task 8 (on wrk, after merge and push): dotfiles sync

- [ ] **Step 1:** `cd ~/dotfiles && git pull --rebase`, then `bin/sync-starter-skills`.
- [ ] **Step 2:** Bring `memory/TEMPLATES.md`'s Procedure File, Changes-state Procedure File and Run Log sections into line with the scaffold's, and its `memory/rules.md` procedure rows with the scaffold's rows (keep dotfiles' other rows and wording).
- [ ] **Step 3: Run** `python3 ~/.agents/skills/personal-memory/gate.py --memory memory audit` -> exit 0; `style-check` on the changed Markdown; `bash tests/run-all.sh` -> pass.
- [ ] **Step 4: Commit** the sync and the memory alignment separately (`personal-memory: sync procedure graduation from starter-agent`, `memory: align procedure template with personal-memory`), push, then `git -C ~/dotfiles push ops-box main`.
- [ ] **Step 5: Report** projects whose own `memory/TEMPLATES.md` copies predate this change (they keep working; list them as side work), with `Checked by: test`.
