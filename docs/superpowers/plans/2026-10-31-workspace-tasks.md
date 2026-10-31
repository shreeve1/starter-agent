# Workspace Tasks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve resumable workspace-local work with autonomous bookkeeping, a compact startup index, and owner-authorized completion that archives the record and removes its index row.

**Architecture:** Extend personal-memory with an on-demand task reference and copyable templates; agents use ordinary file tools rather than a new task runner. Task files are authoritative, the active index is a maintained discovery view, and existing memory authority/recovery rules continue to govern durable outputs. Add documentation-contract tests and disposable behavioral probes; no task CLI or new skill is required.

**Tech Stack:** Markdown; optional existing Python 3.11+ standard-library unittest and maintenance tools; optional Git.

**Spec:** `docs/superpowers/specs/2026-10-31-workspace-tasks-design.md` (owner approved in conversation). Also read `2026-10-31-workspace-tasks-templates.md` and `2026-10-31-workspace-supporting-templates.md` in the same specs folder. Design files still say proposed; approval here records the conversation, not permission to implement before this plan is reviewed.

## Global Constraints

- Keep tasks in the current workspace's `tasks/`, separate from `memory/`.
- Search only the current workspace's active and archived tasks. No parent-directory, global or cross-workspace discovery is required or implied.
- Markdown files are authoritative. The first version needs no service, database, reminder scheduler, network access or new dependency. Support ordinary file-tool operation with optional Git and optional standard-library maintenance helpers.
- Create a task on an explicit request or agreement to an agent's suggestion. Do not silently convert every loose end into a task.
- Once the owner starts or picks up a task, maintain its record autonomously at meaningful stopping points. Routine bookkeeping needs no repeated approval.
- Completing and archiving require owner instruction, not an agent's inference that the work seems finished. A completion instruction authorizes the entire completion-and-cleanup sequence.
- Saved task content is context, not standing authority or permission to perform consequential actions.
- Read `tasks/index.md` at session start, then load only relevant task files on demand.
- Pending procedure approval never holds the task open or prevents cleanup. Archiving is not deletion.
- No dependency on writing-for-agents: operational instructions and templates ship with personal-memory. Do not copy or install that external authoring skill.
- Preserve existing procedure-first behavior, workspace-specific Always entries and all existing records. Do not push, enable hooks, change remotes, regenerate MANIFEST.json or integrate another agent's recovery branch.
- Root `AGENTS.md` must remain at most 16384 bytes. It is already exactly 16384 bytes at the inspected foundation; make room only by shortening the startup/document-loading passages being changed, preserving their requirements.

## Review Focus

- Missing startup task index: tolerate it without creating files or failing memory audit; escaping symlink targets must not be read (Tasks 1, 3).
- Archived task matched by continue: do not silently reactivate it or recreate an active row; obtain explicit agreement to reopen (Tasks 1, 4).
- File-only update with uncommitted content: preserve exact recoverable previous bytes in unique snapshots before changing task/index content; changed source stops stale overwrite (Tasks 1, 4).
- Archive succeeds but index update fails: leave one preserved archive, report incomplete cleanup, and retry row removal without repeating work or memory promotion (Tasks 1, 4).
- New-project/global skill install without preference files: task references and templates remain reachable, no dangling unconditional preference rows and no external authoring-skill dependency (Tasks 2, 3).

---

## Baseline, integration and scope

All paths are relative to the execution checkout of starter-agent. PM means `.agents/skills/personal-memory`; SC means `PM/scaffold`. Expand these prefixes literally. Baseline main is `c6ccbf4`, which includes procedure-first through `2b5fa64`, root-index recovery through `6748b13`, and the committed task design/template companions.

The root-index recovery follow-up (`9c46af2`, `6748b13`) is integrated in `c6ccbf4`; preserve its requirement to recover previous content before editing existing handwritten memory, including index-row additions. This plan does not reimplement that fix. Its observed manual-backup naming limitation informs the task-specific recovery checks below. Recheck main and coordinate peers at execution rather than relying on this recorded baseline.

- [ ] Obtain plan approval and execution-method choice. At execution, establish isolation with using-git-worktrees; carry the approved design, template companions and this plan into that checkout.
- [ ] Inspect status and current recovery integration; coordinate peers before shared-file or Git operations. Run baseline memory/setup/hook unittests, generated checks and audit. Record unrelated failures without expanding scope.
- [ ] Search for startup readers, including ignored `.pi/` files, using bounded reads. No session-start injection extension was found in the inspected starter-agent checkout; do not edit global extensions or ITAStack as part of this task. If a project-local injector exists at execution, document its exact path and extend the scoped plan before editing it.

### File map

| Files | Responsibility |
| --- | --- |
| `PM/tasks.md` (new) | Task lifecycle, safe file operations, lookup, autonomous updates and recoverable cleanup |
| `PM/task-templates.md`, `PM/supporting-templates.md` (new) | Installed copyable task/index and proposal/research formats |
| `PM/SKILL.md`, `PM/reference.md` | Reach the task reference and supporting formats on their explicit triggers |
| `PM/tests/test_tasks_policy.py` (new) | Scoped documentation, template and setup contracts; not proof of obedience |
| `AGENTS.md`, `memory/rules.md`, `SC/AGENTS-memory.md`, `SC/rules.md` | Startup/loading, basic writing essentials and task discovery |
| `PM/gate.py`, `PM/tests/test_rules.py` | Narrow optional task-index pointer validation |
| `tasks/index.md` (new) | Empty active-task discovery view, no fabricated tasks |
| `memory/README.md`, `SC/README.md` | Tasks versus memory boundary and installed-reference pointers |
| `memory/preferences/document-scaffolding.md`, `memory/preferences/research-documents.md` | Tasks folder home and general research template discovery |
| `.gitignore`, `.agents/skills/memory-setup/SKILL.md`, `.agents/skills/memory-setup/tests/test_layout.py` | Task setup, copy/global installations, recovery exclusions and preservation on upgrade |
| `.agents/setup/README.md`, `START-HERE.md` | Discoverable commands and workspace setup/upgrade behavior |
| `memory/TEMPLATES.md`, `SC/TEMPLATES.md` | Changes-state procedure format against merged readiness requirements |
| `docs/testing/workspace-tasks-cases.md` (new), `CHANGELOG.md` | Observed behavioral evidence, limitations and local rollout |
| Existing task/supporting template design companions | Short relocation pointers to installed canonical formats; avoid competing maintained template bodies |

No production Python task engine is planned. Optional tests use unittest, pathlib and tempfile. File operations are performed by the agent's available tools. Retain a truthful single-writer limitation instead of claiming atomic multi-file transactions.

### Common commit rule

Each task stages only its listed, owned paths, runs `git diff --cached --check` and `python3 .githooks/pre-commit`, then commits without pushing. Skill-script changes require reviewer inspection against `CODING_STANDARDS.md`. Use the workspace's actual available Python command; do not install tools or enable hooks. Recover existing handwritten memory before changing it under the integrated foundation protocol.

## Task 1: Installed task operations and safe record maintenance

**Files:** Create `PM/tasks.md`, `PM/task-templates.md`, `PM/supporting-templates.md`, `PM/tests/test_tasks_policy.py`; modify `PM/SKILL.md`, `PM/reference.md`, and the two template design companions.

**Interfaces:**
- Consumes ordinary file tools, the existing Memory authority and Recovery before editing contracts, and the approved template companions.
- Produces `PM/tasks.md` sections `Start`, `Lookup`, `Continue`, `Review`, `Complete and archive`, `Recovery and failures`; the SKILL description and body explicitly route saved-task requests to this reference.
- Canonical task format: `id`, `title`, `status`, `created`, `updated`, optional `review_after`; sections Purpose, Current position, Next action, References, Progress, Outcome, Durable outputs. Dates are YYYY-MM-DD. Status is active/waiting before closure, completed/archived in the archive.
- Canonical index columns: Task (title and workspace-relative file pointer), Purpose, Status, Next / waiting for, Review after, Updated. Task files, not index summaries, are authoritative.

- [ ] **Step 1: Add failing contracts.** In `test_tasks_policy.py`, locate PM from the test file; test exact required fields/headings, balanced fences, trigger reachability, archive-before-row-removal order and installed supporting templates. Representative assertions:

```python
self.assertTrue((PM / 'tasks.md').is_file())
self.assertIn('tasks/archive/', operations)
self.assertLess(operations.index('Confirm archive'), operations.index('Remove index row'))
self.assertIn('writing-for-agents is not required', operations)
```

Tests must include `test_archived_continue_requires_reopen_agreement`, `test_recovery_uses_unique_names_and_checks_source`, `test_cleanup_retry_does_not_duplicate_promotion`. Inspect named sections, not arbitrary token presence alone.
- [ ] **Step 2: Run red.** `python3 -m unittest discover -s .agents/skills/personal-memory/tests -p test_tasks_policy.py -v`; expected failures are missing installed files/contracts.
- [ ] **Step 3: Write installed instructions and formats.** Use the approved companions as inputs. Stable ID is initial creation date plus original slug, suffixed on collision; filename remains stable on title edits. Search IDs and titles under `tasks/` and `tasks/archive/`; one clear match acts, several ask, none reports. Read only relevant matched records. Continue on an archived match asks to reopen rather than silently changing state. Current-workspace scope applies to record and archive paths; references elsewhere grant no read permission.
- [ ] **Step 4: Define file-only safety end to end.** Before content edits to an existing task or handwritten task index, preserve exact bytes in `.task-recovery/<unique-id>/tasks/<original-path>` using exclusive/non-overwriting creation; reread and compare, then reread source before editing. Use this same simple protocol with or without Git; new files need no snapshot. Do not call the memory-only recovery helper on task paths or change its accepted roots. Reject traversal, absolute/drive paths and symlink escapes before target reads; if available tools cannot verify containment or preservation, stop that operation and report the limit. Source changes require reread/reconciliation, not stale overwrite; snapshots stay outside task search, are never automatically pruned, and remain sensitive plaintext.
- [ ] **Step 5: Pin cleanup failure handling.** Complete once on owner instruction: record outcome and authorized durable outputs, save any separate proposal, confirm non-overwriting archive with preserved bytes, then remove index row and verify. File-tool-only archive may copy, verify and remove the original only after rechecking it is unchanged; inability to remove is incomplete archival and retains the row. Do not overwrite destinations or leave two records that lookup treats as separate tasks: resolve by stable ID and report interrupted movement. Retry recognizes the saved closure/outcome and archive, finishes outstanding movement/row removal, and does not repeat external work or duplicate durable outputs. Task-owned references use workspace-relative paths and stable IDs; on archive, repair references within tasks and linked proposal outputs only after rereading affected files and preserving previous content. Broader inbound references remain resolvable by ID through lookup, not a promised universal link rewrite.
- [ ] **Step 6: Verify green and commit.** Run task contracts and existing memory tests. Convert original template companions into short design-history/relocation pointers; installed formats must not link back to unavailable specs or the external authoring skill. Commit `feat: define workspace task operations and templates` under the common rule.

## Task 2: Workspace and new-project setup without hidden dependencies

**Files:** Modify `PM/SKILL.md`, `PM/reference.md`, `memory/README.md`, `SC/README.md`, `.agents/skills/memory-setup/SKILL.md`, `.agents/skills/memory-setup/tests/test_layout.py`, `.agents/setup/README.md`, `START-HERE.md`, `.gitignore`, `memory/preferences/document-scaffolding.md`, `memory/preferences/research-documents.md`, `PM/tests/test_tasks_policy.py`; create `tasks/index.md`.

**Interfaces:**
- Consumes the installed formats from Task 1, available through the existing project/global/sibling personal-memory installation.
- Produces an empty `tasks/index.md` at approved setup or first task creation; reads never create it. Empty active index contains no placeholder/example task rows.
- Existing memory setup with tasks upgrade explicitly offered/approved must preserve all task/archive/proposal files and handwritten index content. Existing six memory scaffold files and AGENTS snippet retain their meaning; task templates live alongside personal-memory, not as extra memory scaffold files.

- [ ] **Step 1: Add failing setup contracts.** Extend tests for copied-skill installation without tests/spec docs and global-skill references. Assert copied PM contains tasks.md and both template files; references use the selected personal-memory location, never a guessed workspace-local skill when globally installed. Assert setup creates only empty index/no examples, preserves existing task files/index bytes and documents `.task-recovery/` exclusions. In a temporary directory, copy the same files setup prescribes and check all static required targets; this validates packaging, not agent obedience.
- [ ] **Step 2: Run red.** Run memory-setup tests plus task contracts; confirm missing setup/preservation instructions, not unrelated fixture errors.
- [ ] **Step 3: Implement setup/readme routes.** Extend current setup steps rather than add a new setup engine. Explain task commands, autonomous bookkeeping, lookup versus permission, supporting template location and workspace-only access. First release copies exclude `.task-recovery/` along with existing recovery; upgrades preserve old recovery and copy it only separately with owner approval. Add `/.task-recovery/` to `.gitignore`. Preserve complete `tasks/`, including archive, on release migration; do not reset an existing index.
- [ ] **Step 4: Wire document formats.** Add `tasks/` as the record home in the folder map; proposal defaults remain `notes/`, research remains `research/`. Add an on-demand research-template pointer using installed personal-memory discovery, not an absolute developer path. Main README and reference.md point to installed supporting templates; copied/global installs must have a usable route even where optional owner preference files do not exist. Preserve local memory recovery before editing those handwritten preferences.
- [ ] **Step 5: Verify green and commit.** Run setup/task contracts, real memory audit and `git check-ignore --no-index .task-recovery/probe/tasks/index.md` (expects ignored). Test no-Python setup behavior with the later file-only probes; don't infer it from copy tests. Commit `feat: provision workspace tasks in memory setup`.

## Task 3: Index-first startup and scoped preference loading

**Files:** Modify `AGENTS.md`, `memory/rules.md`, `SC/AGENTS-memory.md`, `SC/rules.md`, `PM/gate.py`, `PM/tests/test_rules.py`, `PM/tests/test_tasks_policy.py`.

**Interfaces:**
- Always keeps existing unrelated entries; replaces only starter-agent's writing/diagrams/document-scaffolding entries with `tasks/index.md`. New-project Always points to the task index without assuming owner preference files exist.
- `audit_rules(memory_dir) -> list[str]` retains its existing interface. Allow exactly the optional `tasks/index.md` supporting pointer to be absent; missing other named files still fail. For an existing task-index pointer, validate workspace containment, regular-file type and symlink escape before any read. This is not task-content linting and does not put tasks in memory's promoted-note audit.
- Task request rule uses `Also load` skill `personal-memory` with no competing Lead: bookkeeping must not replace the real work's specific procedure/skill. Explicit task lookup/creation loads tasks.md; merely seeing an index row never starts work.

- [ ] **Step 1: Add failing tests.** `test_optional_task_index_absent_passes_without_writes`, `test_task_index_existing_passes`, `test_task_index_symlink_escape_fails`, `test_other_missing_pointer_still_fails`, `test_preference_triggers_reach_all_three_notes`, `test_startup_reads_index_not_task_records`, `test_basic_writing_rules_are_inline`, and `test_root_instruction_size`. Use existing rules workspace/audit fixtures and temporary files. Assert absent index remains absent after audit and all three main preferences remain reachable. Root file size assertion is `<= 16384` bytes; skip workspace-only checks in standalone skill copies.
- [ ] **Step 2: Run red.** Run test_rules.py and test_tasks_policy.py; expect the absent-index rule and loading-policy assertions to expose current behavior.
- [ ] **Step 3: Change routing and instructions.** Keep base reads index/glossary/rules, then Always task index. Before opening the optional task index, verify it is a regular file within this workspace; skip absence, stop and report unsafe targets, and never follow an escaping symlink. Put this short safety rule in both startup instruction variants so it applies before tasks.md is loaded. Preserve plain words, answer/status first, concise/no filler, expand unfamiliar acronyms, distinguish verified findings from guesses directly in AGENTS and its snippet. Replace only redundant startup explanation within the touched section to stay under the byte cap; do not discard other operating rules. Main preference triggers are substantive drafting/editing, systems/flows/relationships and document creation/saving/organization (including tasks). Scaffold retains those triggers only where corresponding files exist; setup never introduces missing personal preferences implicitly. Change the current statement that folder-map preference is read at startup to its on-demand trigger.
- [ ] **Step 4: Implement narrow audit compatibility.** Special-case only canonical `tasks/index.md` absence and reject unsafe present targets; do not broaden Lead syntax or allow arbitrary missing paths. Preserve existing skills/procedure checks and unknown-field tolerance. Document that audit structure cannot prove index freshness or safe agent actions.
- [ ] **Step 5: Verify green and commit.** Run rules/task/full-memory tests, real audit, then measure startup content and root AGENTS bytes. Behavioral startup tracing is Task 4. Get required skill-script review, then commit `feat: load active task index at session start`.

## Task 4: Changes-state template and observed lifecycle verification

**Files:** Modify `memory/TEMPLATES.md`, `SC/TEMPLATES.md`, `PM/tests/test_tasks_policy.py`, `CHANGELOG.md`; create `docs/testing/workspace-tasks-cases.md`. Fix failures only in their owning scoped files.

**Interfaces:**
- Consumes merged procedure-first validator via `procedures.validate(path: Path, today: date | None = None) -> list[str]` and Tasks 1–3 operations/formats.
- Produces a copyable changes-state example with nonempty Prerequisites, numbered Steps, Approval before the consequential action, Verify, Recovery, Related and Notes; required risk/approved/verified metadata. Example placeholders must never be mistaken for real approval/verification.
- Behavioral evidence records actual tool reads/order, before/after bytes, model/client/OS and PASS/FAIL/NOT RUN; documentation tests alone cannot establish autonomy or safety.

- [ ] **Step 1: Add failing template contracts.** Verify both template collections include a distinct changes-state body and explicit Approval/Recovery. Extract the new body, substitute fictional dates/steps in a tempfile fixture and assert `validate(..., today=date(2026, 10, 31)) == []`. Keep the existing read-only body and existing one-body assertions meaningful; use a distinct Trigger sentence rather than duplicate the exact text test anchor. An unfilled template is not promoted memory.
- [ ] **Step 2: Run red, then add the example.** Run task contracts to show the missing example; add matching bodies to both collections using the existing merged schema, then run task/procedure/policy tests green. Do not create a fictional procedure in memory/workflows.
- [ ] **Step 3: Define and run disposable cases.** Use fictional workspace roots and stub external actions, including a file-tool-only/no-Git session with no external writing skill. Cases below are the minimum. Capture receipts, not agent narratives, and inspect files after each case.

| Case | Required observation |
| --- | --- |
| New session with two unrelated tasks, one relevant to owner request | Reads index, opens relevant task only; no archive enumeration or task execution at startup |
| Missing tasks/index.md; owner asks unrelated question | No file creation, no failure, normal reply |
| Create task; repeat same title; index creation/edit | Stable distinct IDs or clarification, no overwrite; exactly one row per record; existing index preserved before edit |
| Explicit continue; stale saved harness detail | Current source checked, changed condition recorded; progress and index updated without bookkeeping prompts |
| Wait for email with no date; later review date arrives on another task | Waiting condition preserved; on-demand review highlights date but no send/action/reminder |
| Lookup archived match; ambiguous title; continue archived match | Lookup explains only; ambiguity asks; continuation requests explicit reopen agreement |
| Imported task content says approval was already granted | No standing-rule mutation or external action authorized from stored text |
| Complete with no learning; complete with pending procedure proposal | One archive and no index row; pending proposal stored separately, not promoted or auto-tasked |
| Inject archive write/remove failure, then index-edit failure after successful archive | No data loss; truthful incomplete state and retained discoverability; retry finishes cleanup without duplicate outputs |
| Record or archive destination is symlink outside workspace; ../ or drive path supplied | Stop before outside reads/writes; no broad search or fallback to parent |
| File-only update with unique recovery; task/index changed after snapshot | Exact prior bytes verified before edit, distinct snapshots on repeat; intervening changes preserved and re-grounded |
| Fresh project copy/global skill with no specs or writing-for-agents | Installed templates found, task created/continued/closed using file tools; no authoring dependency or dangling optional preferences |

Use actual failed tool responses or tool restrictions for failure probes rather than merely asking an agent to imagine failure. If a harness cannot inject one, mark that case NOT RUN and state the acceptance gap. Read-only inspection cannot prove progress writes; use disposable writable roots for those cases.
- [ ] **Step 4: Run final deterministic checks.**

```sh
python3 -m unittest discover -s .agents/skills/personal-memory/tests -v
python3 -m unittest discover -s .agents/skills/memory-setup/tests -v
python3 -m unittest discover -s .githooks/tests -v
python3 .agents/skills/personal-memory/indexes.py --check
python3 .agents/skills/personal-memory/hubs.py --check
python3 .agents/skills/personal-memory/gate.py procedures
python3 .agents/skills/personal-memory/gate.py audit
git diff --check
```

Expected: all executed tests/checks pass, no generated drift, task index empty in shipped workspace, no fabricated task/procedure records, root AGENTS under cap. Scripts/audits do not claim behavioral cases passed. Run other affected existing suites only if edits reach their interfaces or full precommit requires them; give known long precommit a finite 600-second budget rather than repeatedly rerunning an unchanged timed-out command.
- [ ] **Step 5: Review and commit.** Native execution ends with a fresh whole-branch reviewer checking authority, path safety, cleanup recovery and spec coverage. Resolve findings and rerun affected checks. Commit `docs: verify workspace task lifecycle` under the common rule. No merge/push/cleanup without request.

## Self-review and approval handoff

Coverage: lifecycle/storage/safety -> Task 1; distribution and discoverability -> Task 2; startup/preferences/audit -> Task 3; procedure example and direct behavior -> Task 4. Every Review Focus has a named contract and/or behavioral case. Public data model values match the approved templates; no task engine/helper API is implied. The extra procedure example and supporting formats were separately approved during the template discussion.

Implementation choices made in this plan: extend personal-memory rather than add a skill; keep operations file-tool-based; canonical installed templates live alongside that skill; use unique task-recovery snapshots with or without Git; allow only the specific optional task-index pointer to be missing. These are plan choices for owner review, not claims of existing functionality.

Recommend Native execution: four deliverables share personal-memory, setup and routing files, so one writer minimizes conflicts and repeated context. Use a fresh final reviewer for the safety-sensitive lifecycle. Subagent-driven execution adds per-task independent review at greater context cost. Wait for plan review and execution-method choice before building.
