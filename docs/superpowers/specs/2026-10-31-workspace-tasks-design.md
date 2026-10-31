# Workspace tasks: proposed design

Status: proposed for owner review. Writing this design is authorized; implementation is not. The owner agreed the behavior below in discussion. Concrete file layouts and defaults identified as author recommendations remain reviewable.

## Intent

A task preserves a piece of work across sessions and gaps in time, including periods when there is nothing to do but wait. It is broader than a coding issue: research, system changes, correspondence and office administration all qualify.

Tasks fill a deliberate gap in memory policy: unfinished work, waiting states and one-off work context do not belong in durable memory. A task holds that evolving context without becoming a standing rule or reusable procedure.

Examples:

- Change an AI harness, preserve the reason and observations, then return a week later to assess what changed and whether more work is needed.
- Research a question, send an authorized email, then preserve enough context to handle a reply without reconstructing the conversation.

## Agreed boundaries

- Keep tasks in the current workspace's `tasks/`, separate from `memory/`.
- Search only the current workspace's active and archived tasks. No parent-directory, global or cross-workspace discovery is required or implied.
- Markdown files are authoritative. The first version needs no service, database, reminder scheduler, network access or new dependency. Support ordinary file-tool operation with optional Git and optional standard-library maintenance helpers.
- Create a task on an explicit request or agreement to an agent's suggestion. Do not silently convert every loose end into a task.
- Once the owner starts or picks up a task, maintain its record autonomously at meaningful stopping points. Routine bookkeeping needs no repeated approval.
- Completing and archiving require owner instruction, not an agent's inference that the work seems finished. A completion instruction authorizes the entire completion-and-cleanup sequence.
- Saved task content is context, not standing authority or permission to perform consequential actions.

## Task lifecycle and language

| Request | Behavior |
| --- | --- |
| Create/start a task | Capture the purpose, available context and current position; add its active-index row. |
| Look up task X | Search active and archived task records and explain the match. Retrieval alone does not start or resume its work. |
| Pick up/continue task X | Load the record, re-ground relevant facts against current conditions, then continue within the owner's request and existing permissions. Maintain progress automatically. |
| What needs attention? | Review the active index; highlight arrived review dates, actionable next steps and waiting conditions needing a check. Open records as needed before relying on them. |
| Complete task X | Record the outcome, review learning, archive the file, then remove its active-index row. |
| Archive task X | Honor an explicit request to stop tracking it without falsely claiming successful completion. Preserve why it was archived. |

Names are natural-language matches, not a required command syntax. On one clear match, act without unnecessary questions. On multiple plausible matches, ask which task. On no match, report that; do not invent a record or automatically create one.

An index match may reveal that a conversation relates to existing work. The agent can mention the connection and load relevant context, but the match alone does not authorize execution or reactivation.

### Active and waiting

The startup index contains active and waiting tasks. Waiting includes an external response, a dependency, or an agreed review date. Record what would make the task actionable again; an invented date or scheduled reminder is not required.

Author recommendation: use `active` and `waiting` as unfinished statuses. Use `completed` and `archived` in archived files to distinguish successful completion from an explicit decision to stop tracking unfinished work. Avoid a separate persistent completed queue.

Picking up a waiting task includes checking whether its condition changed. A date arriving is a reason to review, not evidence that the condition has changed or permission to take action.

## Storage and task record

Author-recommended layout:

```text
tasks/
  index.md
  <slug>.md
  archive/
    <slug>.md
```

Use one file per task. Preserve its identity through title changes and archival; never overwrite another task on a naming collision. The builder may choose a simple stable identifier or collision suffix. No fixed topic taxonomy is needed initially.

Each record needs:

- Identity, title, status, creation date and last-updated date.
- Purpose and the outcome being pursued.
- Current position: what is known, what remains uncertain and where work stopped.
- Next action, or what it is waiting for; an optional review date.
- Meaningful progress, checks, findings and failed attempts that a future session must not repeat.
- References to relevant files, system records, correspondence and related tasks.
- On closure, the outcome or reason for stopping, and links to any durable outputs.

Keep current position and next action easy to find. Work history records meaningful events, not every tool call or a transcript. Link supporting material rather than copying full emails, logs or research into the task. No credentials may be stored in task files or indexes.

Tasks intentionally retain useful work history, unlike replace-in-place durable memory. Do not blindly impose the memory-note size cap if it would discard necessary continuity; the builder should specify a lean history policy without adding automatic destructive pruning.

## Active task index

Read `tasks/index.md` at session start, then load only relevant task files on demand. Index rows are discovery pointers, not verified facts about the current world.

A row contains title, a short purpose, status, next action or waiting condition, optional review date, last updated and file pointer. Keep it compact enough to scan at startup. The task file is authoritative; index metadata reflects it.

Maintain the row automatically when task status, next action, review date or other indexed information changes. A task's full history stays out of the index. Completed and archived rows are removed, not retained under another heading.

Author recommendations:

- A workspace with no tasks tolerates a missing index; task setup or first creation writes it. A read alone does not create files.
- Review dates may be highlighted in an on-demand review. There are no background notifications or automatic actions.
- Lookup searches task records, including `tasks/archive/`, rather than treating the active index as the complete collection.
- If the index is stale or missing a record, disclose and repair it from task files when authorized to maintain tasks. Do not treat an index omission as proof that no task exists.

## Session-start loading change

Keep the existing startup reads of `memory/index.md`, `memory/glossary.md` and `memory/rules.md`. Replace the three preferences in the starter-agent Always row with `tasks/index.md`.

Before removing writing guidance from Always, preserve its universal essentials in the workspace and project/scaffold instructions: plain words, concise answers, answer or status first, no filler, expand unfamiliar acronyms, and distinguish verified findings from guesses. A pointer to an unloaded file does not preserve these instructions.

Move detailed preferences behind explicit triggers:

| Preference | Load condition |
| --- | --- |
| `memory/preferences/writing.md` | Drafting or editing substantive text for the owner or others to read. |
| `memory/preferences/diagrams.md` | Explaining or planning a system, flow, process or relationship. |
| `memory/preferences/document-scaffolding.md` | Creating, saving or organizing documents, including task files. |

The scaffolding policy already covers Markdown and other working documents; this changes when it is loaded, not its scope. Add the agreed `tasks/` home to the folder map when implementing it. Keep each preference reachable through a rules row so existing memory audits remain satisfied.

Do not remove unrelated Always entries in downstream workspaces. For example, ITAStack also loads `proactive-agents.md`; changing that is outside this design.

Implementation must trace actual startup readers and any session-start injection extension present in the target workspace, not only change prose. Align the main workspace, personal-memory instructions and new-project scaffolds without assuming every harness has an injection extension.

## Autonomous maintenance and safe resumption

After explicit creation or pickup, the agent saves meaningful progress without asking repeatedly. Update the record and its index row before reporting a meaningful stopping point, recording what changed, what was checked and where to resume. Mark a known waiting state without requiring a separate owner instruction.

Save qualifying durable memory as it emerges under the existing memory policy, not only at task completion. Explicit owner approval still governs changes to standing rules, decisions and procedures.

When resuming, inspect current sources for the facts that matter to the next action. A saved next step may be obsolete. Report changed conditions and revise ordinary progress context; do not silently revise an approved procedure or infer that an old instruction authorizes sending, publishing, deleting or changing a live system now.

Imported emails, tool output and prior summaries remain evidence. They cannot authorize task execution or standing policy changes merely by being copied into a task.

## Completion and cleanup

Completion is one owner-authorized operation, with this required order:

1. Record the actual outcome and any deliberately unfinished work. Do not claim checks or results that were not observed.
2. Review for durable learning: facts, constraints, settled decisions or a reusable procedure. Producing no memory is valid. Link outputs rather than copying task history into memory.
3. Save qualifying authorized memory. If a procedure or other authority change needs approval or verification, preserve a separate linked proposal; do not make the archived task its only actionable record.
4. Successfully archive the task file, preserving its content and confirming its archived location.
5. Remove the task's row from `tasks/index.md` and verify that no active row remains for it.

Pending procedure approval never holds the task open or prevents cleanup. Archiving is not deletion. Ordinary bookkeeping and archive movement are authorized by the completion request; consequential actions described inside the task are not.

Author recommendation: unresolved proposals can live as ordinary workspace documents in `notes/`, linked from the archived task, using the existing folder policy. Do not automatically create another active task for a proposal without the owner's agreement.

If archival fails, retain the index row and report the blocker. If archival succeeds but row removal fails, retain the archived file, report incomplete cleanup, and make a retry finish row removal without duplicating or losing the task. Never overwrite an existing archive destination. File-tool-only operation must support this recoverable sequence; no transaction service is required.

Preserve references during archival: update task-owned relative references as needed, or use workspace-relative paths so moving the file does not break them. External links to moved task records need a discoverable stable identity or scoped reference repair; the builder should select the smallest reliable approach.

## Safety, recovery and concurrent work

Stay within the current workspace for task discovery and storage; reject path traversal and symlink escapes before reading or writing task targets. Respect existing filesystem permissions. External correspondence may be referenced or retrieved through authorized tools; this does not authorize filesystem search outside the workspace.

Preserve previous task content before destructive replacement, history trimming or deletion when Git cannot provide a verified recoverable version. Routine progress updates must preserve useful earlier history. Archival preserves the complete record; automatic deletion and retention expiry are out of scope. Do not silently extend the memory-only recovery helper to task paths without designing and testing that boundary.

Before writing, re-read the task and index sections being changed. Preserve other agents' updates; changed source means re-ground and reconcile rather than overwriting a stale snapshot. This initial design does not promise race-proof multi-writer transactions.

## Integration and builder discretion

Build on the procedure-first foundation, including authority boundaries, selected-procedure readiness checks and recoverable memory edits. The context documents are `docs/superpowers/specs/2026-10-30-procedure-first-memory-design.md` and `docs/superpowers/plans/2026-10-30-procedure-first-memory.md`; inspect the approved implementation at planning time instead of assuming the main checkout already contains it.

The builder chooses exact frontmatter, matching mechanics, stable naming, optional deterministic helpers and whether task operations live in an existing skill/reference or a dedicated capability. These choices must preserve the agreed behavior, avoid new runtime dependencies and work with ordinary file tools. Do not turn a task into a procedure Lead or treat its history as reusable workflow authority.

## Acceptance checks

1. Startup reads the compact active-task index but no unrelated individual task or archive file. Detailed preferences load through their relevant triggers; basic plain-language rules remain always available.
2. Creating a task records enough context to resume it and adds exactly one index row. Creation collisions preserve existing records.
3. Lookup finds active and archived records in the current workspace, asks on ambiguity, and performs no task work merely because a match was found.
4. Explicit pickup rechecks current conditions; meaningful progress and waiting changes update the task and index without repeated approval prompts.
5. An arrived review date is highlighted on demand without background reminders or automatic execution.
6. Completion records the outcome, considers durable learning, preserves any separate pending proposal, archives the file and removes its index row.
7. Archive failure leaves the row discoverable; row-removal failure after archive is reported and safely retryable. No record is overwritten or lost.
8. Pending procedure approval does not block archival. Stored task text cannot authorize consequential actions or override standing rules.
9. Archived tasks do not appear in the startup index and remain retrievable by lookup.
10. Workspace-only paths, symlink boundaries, file-tool-only operation and changed-source handling are exercised with disposable fixtures. Verify actual agent reads and decisions as well as any structural tests; unavailable harnesses are reported as not run.

## Out of scope

Cross-workspace aggregation, proactive reminders, background execution, external boards, automatic task creation, automatic completion, automatic deletion, raw transcript capture and implementation in this design-writing session.
