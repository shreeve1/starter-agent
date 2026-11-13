# Procedure graduation: design

Date: 2026-11-12. Status: approved by the owner 2026-11-12, including the calls listed at the end. Covers two workspaces and one sync:

- itastack: `~/Documents/itastack` (no Git; Syncthing; the owner's IT client workspace).
- starter-agent: `~/starter-agent` (Git; the template other agent workspaces are built from).
- dotfiles: `~/dotfiles`, which receives starter-agent's `personal-memory` skill through `bin/sync-starter-skills`.

"The owner" (in itastack, "the operator") is James.

## Intent

Agents should propose procedures from real work. Each procedure then climbs a short ladder toward running its safe steps without asking. At the end of every run, the session asks whether to review how it went, so a procedure gets fixed when it drifts and moves up when it has earned it.

A review on 2026-11-12 found the loop broken:

- itastack has most of the parts (draft procedures, per-run rows in a runs file, per-step trust the operator grants, automatic revocation on a failed readback, Harvest at ticket close), but nothing connects them. All 14 procedures are still `draft`. The Mallory deactivation procedure has 8 recorded runs and was never offered for trust. The run card agents follow (`halo-ticket-research/references/procedure-run.md`) ends at the email and close, so no review happens. Only 12 of 72 closed research files record a Harvest decision. A proposed shared procedure (`A-71050-3`, FortiGate conserve mode, 2026-10-27) has waited 16 days, because the weekly look-back that would list it never runs (`.agents/startday.json` does not exist).
- itastack's `reviewed` status is defined as "a run where every step passed", which a branching procedure rarely meets, and nothing uses it. "Suggest trust" sits only in the long research skill, says "3 `pass` rows" where the decision note says 3 runs, and project research and chat runs record no rows.
- starter-agent forbids the goal outright: "Stored procedure approval does not authorize the current action." Every state-changing step asks every time, procedures are written only after an owner-approved verified run, and there is no draft status, no run record and no ladder.

## Decisions settled with the owner (2026-11-12)

| # | Decision |
|---|---|
| D1 | One shared design, built natively in each workspace. itastack first (mostly wiring existing parts), then starter-agent (copying what proved out), then the usual dotfiles sync. Rejected: porting itastack's Halo-specific scripts into starter-agent (they assume Halo tickets, and starter-agent must work without Python); moving itastack onto a new general engine (rewrites the trusted Mallory create flow stabilized on 2026-11-09). |
| D2 | starter-agent reverses "stored approval never covers the current run". A trusted step of a trusted procedure runs on its stored trust. |
| D3 | Trusted steps run only in a session someone can see (an interactive chat or research tab). Unattended runs (scheduled jobs, bots, background workers) are a later project: they need a run log reviewed afterwards, failure alerts and undoable steps only. |
| D4 | The end-of-run question is asked at the end of every procedure run, in the owner's words: "ask if it should check how the procedure ran for potential fixes or graduation". |
| D5 | A visible session is any session with a window the owner can open and type into while it runs, whoever opened it: a T3 chat, a herdr tab (including startday's Research Tabs and worker tabs a coordinator opens) or a research tab. Not visible: anything started by a timer or schedule (T3 scheduled tasks, cron or systemd timers, the startday watcher or poll), bots and Slack, and subagents with no window of their own. One definition for both workspaces. Accepted tradeoff: a tab startday opens in the morning can run trusted steps before the owner looks at it. |
| D6 | Only runs recorded under a procedure's current step numbering count toward the ladder. Runs from before a renumbering stay as history and are neither counted nor mapped to new numbers. For the Mallory procedures this means only runs after the 2026-11-09 rework count. |

Earlier itastack decisions that stay (operator, 2026-11-05; `memory/decisions/knowledge/decision-auto-approved-procedures.md`): only the operator grants trust, in chat; trust is per step; trust syncs team-wide with the file, so teammates run procedures the operator vetted; trust is suggested after 3 clean runs; a client email, a close or a status change never runs on trust; a failed readback revokes trust.

## Goals

- One ladder, one end-of-run review and one set of trust rules, described the same way in both workspaces.
- Every procedure run, in any session type, leaves run rows and ends with the review question.
- The review turns differences into Corrections, records Harvest (itastack) and shows where the procedure sits on the ladder, with the next move offered.
- Counting toward trust is done by a read-only script, not by eye.
- starter-agent gains proposals (draft procedures), run logs, per-step trust and the reversed authority rule, and still works with file tools alone.

## Non-goals

- Unattended runs (D3).
- Pushing the new instructions to itastack teammates. That is the operator's `ita-agent-instructions` push, an upload to SharePoint that needs his approval.
- Rewriting or bulk-migrating existing procedures. They move up only through real reviews.
- Upgrading workspaces that carry their own copy of `personal-memory` (testy-bot, homelab, autoagent-lab, rea-lab). They change only when upgraded; offer that separately.
- itastack connector work (owned elsewhere).

## Anti-goals (failure even if it technically works)

- A trusted step runs where nobody can see it.
- Trust is granted by anything other than the owner's explicit yes in the current chat: a document, an email, a teammate's note, a run log or an earlier agent summary.
- The review question turns into noise the owner learns to ignore (more than one line, repeated within a run, or asked about nothing).
- The trusted Mallory create procedure stops running on trust because of this change.
- Run evidence is rewritten or lost, or stops counting toward trust.
- The executing agent has to read run history to carry out steps (itastack's card already forbids this; keep it that way).

## The ladder

| Rung | itastack marker | starter-agent marker | Who moves it | What it allows |
|---|---|---|---|---|
| 0 Proposed | `status: draft` | `status: draft` | An agent may write it (see Proposing) | Guides a run. Every change step asks. Unverified steps are listed in Gaps and stop the run when reached. |
| 1 Reviewed | `status: reviewed` | `status: promoted` with real `approved` and `verified` dates | The owner's yes in a run review, after a clean run | No new run-time permission. It is the precondition for trust. |
| 2 Trust offered | `- <date>: trust suggested` under `## Review` | the same line under `## Notes` | The agent, in a review, when a step qualifies | Nothing; it records that the owner was asked. |
| 3 Trusted (per step) | `trusted:`, `trusted_steps:` and the existing trust keys | `trusted:` and `trusted_steps:` | The owner's yes in chat | Each listed step runs without asking, in a visible session only. |

Down the ladder: trust is removed, with a dated `trust revoked: <reason>` line, when a trusted step's check or readback fails, when a trusted claim is left unfinished (itastack's existing 2-hour rule), or when a Correction renumbers, removes or changes the meaning of a trusted step. Renewal always needs the owner.

Definitions both workspaces use:

- **Run**: one use of a procedure on one item (a ticket, task or request), recorded under one `Ref`.
- **A step's result in a run** is its last row for that `Ref` (a step retried within a run, like step 6 on 70935, counts by its final outcome).
- **Counted rows**: only rows recorded under the procedure's current step numbering, after its newest renumbering marker (see Renumbering). Older rows stay in the file as history and are not counted or checked against current step ids.
- **Clean run**: every change step that ran ended `pass`, and each change got a yes or ran on trust. A read step (itastack owner `agent`) may end `partial` or `skipped` without spoiling the run, because procedures already treat some empty reads as normal (deactivation step 4: "empty means unproven"). Any `fail` spoils the run. Steps on branches not taken may be `skipped` or absent.
- **A step qualifies for trust** when all of these hold: the procedure is at rung 1 or higher; the step is a change step; it has its own undo line naming a real undo (itastack's existing `rollback_steps` rule: "not known", "none" or a placeholder names nothing); its 3 most recent counted results since the last trust change are `pass`, from 3 different runs; and it is not on the never-trusted list.
- **Never trusted**: a message to another person (a client email); closing a ticket or changing its status; spending money; a browser fallback row (itastack `W` rows); any step with no real undo. These always wait for a yes.
- **Visible session**: as defined in D5. Trusted steps run only in visible sessions, in both workspaces.

itastack's existing trust keys stay as they are (`authorizes`, `match_client_id`, optional `match_summary_prefix`, the `doc` source rule for `client-change`). starter-agent has no ticket system, so its trust is scoped by the procedure's Trigger and Prerequisites and checked by the step's Verify.

**Shared procedures (itastack).** Trust is client-scoped, so a Shared Procedure climbs per client through that client's override file (`overrides:` plus its sibling runs file), which `validate.py` and `sd.py trust` already support through `merged_steps`. A run on a client ticket writes its rows to that client's override runs file, creating the stub if missing (the existing rule). The shared file itself reaches `reviewed` through a review of any client's clean run; the status change is a Correction, saved in place under the existing rule. A run with no client records no rows; the question is still asked.

**Renumbering.** A Correction that renumbers steps, removes one or changes a step's meaning writes a dated marker in the runs file that makes clear which `Ref` is the first under the new numbering. For the two Mallory procedures, the build adds the 2026-11-09 rework marker so that 71188 (recorded under old numbers) falls before it. `validate.py`'s `reviewed` result checks, the ladder report and trust counting read counted rows only, so marking Mallory create `reviewed` cannot fail validation on legacy step ids and turn off its trust.

Example from today's data (D6): the 2026-11-09 rework renumbered both Mallory procedures and moved their steps to connector operations, so Mallory deactivation has one counted run (70935, 2026-11-12) and Mallory create has none. Deactivation steps 5, 7, 8, 10 and 12 have real undo lines and passed on 70935; after two more clean runs they would be offered, once the procedure is reviewed and has `authorizes: client-change` and `match_client_id`. Steps 6 and 11D have no known undo and would always ask.

## Proposing procedures (rung 0)

**itastack.** The existing paths stay (`procedure-capture`: a Client Procedure saves as `draft` automatically; a new Shared Procedure or a promotion is a `procedure-change` approval). Two fixes:

1. Harvest runs whenever a ticket that followed a procedure, or could yield one, is closed in a session, including a close the operator directed in chat. The ticket's research file always gets `harvested` or `harvest_rejected`.
2. startday's daily run lists `procedure-change` drafts still waiting, with their age, so a proposal is not lost while the weekly look-back is off. Whether to turn the look-back on is a separate choice for the operator.

**starter-agent.** When the owner performs or describes a repeatable workflow and no procedure covers it, the agent may save a `status: draft` procedure in `memory/workflows/<topic>/<slug>.md` and report it in one line (`Procedure proposed: <path>`), the same way it reports saved memory. A draft needs Trigger, Prerequisites, numbered Steps, Verify, Related, Notes and a `### Gaps` section listing every step not yet run and verified (`None.` when all were); `approved` and `verified` stay empty until a review promotes it. Changes-state drafts also need Approval and Recovery. Dates are never invented.

## The end-of-run review

**When.** A procedure run ends: it finished, stopped at a stop condition or a failed step, or the owner ended it. Any session type: in itastack ticket research, project research or a plain chat; in starter-agent any session that followed a procedure.

**Always, before asking.** Record the run rows (one per step that ran or was deliberately skipped). itastack already does this for ticket research; project research and chat runs must do it too. starter-agent writes them to the new run log.

**The question.** One line, once per run: "Review how this run went?" When something is ready, add one short clause, for example "steps 5, 7, 8 and 12 now qualify for trust" or "this was a clean run; it can be marked reviewed". No answer, or no, ends it; the rows stay.

**On yes, in order:**

1. **Differences.** For each step that behaved differently from the procedure, propose a Correction. itastack keeps its existing authority: Client Procedure Corrections and Shared Procedure Corrections are saved in place and reported; new Shared Procedures and promotions go through a `procedure-change` approval. starter-agent keeps its existing authority: the agent shows the edit and saves it on the owner's yes.
2. **Harvest (itastack).** If the ticket is closed and its research file has no Harvest decision, run Harvest now.
3. **Ladder.** Run the ladder report (below) and show its result in plain words: the current rung, what the next rung needs, which steps qualify for trust, and which are blocked and why (for example "step 10: 1 clean run of 3", "step 6: no known undo"). Offer the next move: "mark it reviewed?" after a clean run, or "trust steps 5, 7, 8 and 12?" when steps qualify. Write `- <date>: trust suggested` when trust is offered.
4. **Apply on yes.** Reviewed: set the status (itastack `reviewed`; starter-agent `promoted` plus `approved` = today and `verified` = this run's date). Trust: itastack adds any missing trust keys and Rollback lines as a Correction, then runs `sd.py trust <path>`; starter-agent's agent writes `trusted:` and `trusted_steps:` after `gate.py procedures` passes the trust rules.
5. **Summary.** End with one line, for example `Run review: 1 correction saved, harvest recorded, steps 5, 7, 8 and 12 trusted.`

The unprompted itastack "Suggest trust" rule (once per procedure per 7 days) folds into this review: the readiness clause on the question replaces it, and the 7-day limit applies only to repeating the clause, not to a review the owner asked for.

**Ladder report.** A read-only command reads the procedure and its counted run rows and prints the rung, each change step's status (qualifies, or the reason it does not) and the next move. It writes nothing. itastack: a `sd.py` subcommand, since `sd.py` and `validate.py` already parse procedures and runs files; for each counted `pass` of a change step it also looks in `artifacts/startday/ledger.jsonl` for a finished approval naming that procedure, step and ticket, and reports a pass with no matching approval instead of counting it silently. starter-agent: a `gate.py` subcommand that counts rows (it has no ledger; the owner's yes to trust is the final check), plus the same counting rule written out for file-only use.

## Running trusted steps

itastack keeps its existing mechanics (`approval trusted`, live guards, readback, `approval finish`, revocation).

starter-agent, new:

- Before the run, `gate.py procedures <path>` must pass, including the trust rules. A failure means no step runs on trust in this run.
- Without Python, no step runs on trust: the agent cannot run the checker, so every change step asks. File-only workspaces still get proposals, run logs, the review and the hand-counted ladder; they just never skip a yes.
- A trusted step runs without asking only in a visible session (D5). Any other session treats every step as untrusted.
- Before each trusted step, the agent checks the step's prerequisites and stop conditions against the current state. After it, it runs the step's Verify. If Verify fails, it stops, removes `trusted:`, adds `- <date>: trust revoked: <reason>` under Notes and tells the owner.
- Every other change step still asks in the current conversation.

## itastack changes

- `halo-ticket-research/references/procedure-run.md`: Finish gains "record the run rows, then the end-of-run review"; one place for the review steps; the card applies to ticket research, project research and chat runs.
- `halo-ticket-research/SKILL.md`: Step 9 "Worked runs" and "Suggest trust" point to the card; Harvest is also triggered by any in-session close; "3 `pass` rows" becomes 3 runs.
- `halo-project-research/SKILL.md`: record run rows and run the review through the card.
- `memory/rules.md`: a row for following a Procedure in any session that loads the card.
- `procedure-capture/SKILL.md` Step 5 and `references/template.md`: `reviewed` means the operator confirmed it in a review after a clean run, replacing "every step passed".
- `startday/scripts/sd.py`: the ladder report subcommand; `sd.py trust` refuses a new grant on a `draft` procedure (an already-trusted file keeps validating and running, so Mallory create is unaffected; its next review will offer "mark reviewed"); the daily list of waiting `procedure-change` drafts.
- `startday/SKILL.md` and `startday/references/formats.md`: the daily list, the ladder report and the `reviewed` meaning.
- `CONTEXT.md` (Procedure, Trusted Procedure, Harvest terms), the three procedure decision notes under `memory/decisions/knowledge/` and `memory/decisions/halo/decision-live-change.md` (which defines `reviewed`): the ladder and the review.
- `CONTEXT.md` Live Change ("Only a visible session makes one") and the trusted-procedure decision note: state the D5 definition, so both workspaces read the same rule.
- Tests: the startday and procedure-capture suites; every existing procedure still validates.

## starter-agent changes

- Procedure File templates (`memory/TEMPLATES.md` and `scaffold/TEMPLATES.md`): `status: draft` or `promoted`; `### Gaps` for drafts; optional `trusted:` and `trusted_steps:`; per-step undo lines `- Step <n>: <how to undo>` under `### Recovery`, required for each trusted step; dated trust lines under `## Notes`.
- Run log `memory/workflows/<topic>/<slug>.runs.md` beside its procedure: `type: worked-runs`, `procedure: <path>`, the same 6-column table as itastack (`Ref`, `Date`, `Step #`, `Actual action`, `Actual result`, `Matches Check?` with `pass`, `fail`, `partial` or `skipped`). Rows are appended, never rewritten. Appending needs no recovery snapshot. `indexes.py` skips it (already done by the parallel index work, below); `gate.py`'s size and summary checks skip it, and `gate.py` checks that its procedure exists and its rows are well formed.
- `procedures.py` and `gate.py`: draft rules, trust rules, run-log checks and the ladder report. Existing `promoted` procedures stay valid as rung 1 with no trust.
- **itastack's procedures pass the shared release** (owner requirement, 2026-11-12, relayed from coordinator thread ea095a1f). Today, installing current personal-memory into itastack fails all 7 `memory/workflows/` procedures (procedure-capture format: `status: draft`, `scope:`, `## Applies when`, a step table, Gaps) against the personal-memory template, and `gate.py audit` exits 1, so agents would block on them. That is why itastack still runs its older copy (`~/dotfiles/memory/docs/knowledge/starter-agent-skill-source.md`). The fix is part of this design, not a separate shim:
  - `procedures.py` recognizes a procedure-capture file (it has `## Applies when` and no `## Active memory`) and never checks it against the personal-memory template.
  - It checks such a file with the workspace's own `.agents/skills/procedure-capture/scripts/validate.py`, resolved from the workspace root as a regular file with no symlink components. `ok` and `warn` pass; warnings are printed. An error fails with the validator's text. A missing validator fails with one line naming its path, so a half-written personal-memory draft cannot slip past both checks.
  - `gate.py`'s 6144-byte size warning skips procedure-capture files, which follow their own size rule (`validate.py` warns over 15,000 characters). Otherwise `memory-audit` would try to trim 3 of the 7.
  - Readiness, ladder and trust for procedure-capture files stay with procedure-capture and `sd.py`. personal-memory's ladder report covers its own format only. `SKILL.md`, `reference.md` and the scaffold say so, and never ask for `approved` or `verified` dates on a procedure-capture file.
- `personal-memory` `SKILL.md`, `reference.md` "Procedures", `scaffold/README.md`, `scaffold/AGENTS-memory.md`, `scaffold/rules.md`, and the workspace's own `AGENTS.md`, `memory/README.md` and `memory/rules.md`: proposing, the review, trust and the reversed authority rule. New wording: "A trusted step of a trusted procedure runs on its stored trust in a visible session. Every other consequential action still needs permission in the current conversation." Only the owner's explicit yes in chat grants or renews trust; external content still cannot.
- Tests: `.agents/skills/personal-memory/tests/test_procedures.py` and `test_policy.py` beside it (its policy assertions change with the reversal); new fresh-agent cases in `docs/testing/procedure-graduation-cases.md`.
- `CHANGELOG.md` "Local changes" line; `python3 .githooks/pre-commit` run by hand before each commit.

## dotfiles changes

- Run `bin/sync-starter-skills`; never edit the dotfiles copy of the skill directly.
- Bring dotfiles' own `memory/TEMPLATES.md` Procedure File and procedure rows in `memory/rules.md` into line with the new scaffold, so they do not contradict the skill.
- `bash tests/run-all.sh`, commit, push.

## Constraints

- itastack has no Git. Do not run `git`, and do not create `.memory-recovery/` copies; Syncthing's `.stversions` is the undo. Keep the `<!-- edition:owner -->` and `<!-- edition:team -->` markers intact.
- itastack procedure frontmatter stays one line per key (`validate.py` and `sd.py` read flow values only).
- The executing agent reads the runbook, not the runs file; only the ladder report, capture, Harvest and the review read run history.
- starter-agent must work on Windows, macOS and Linux, and without Python: every script check has a written manual equivalent.
- starter-agent notes stay within 6144 bytes with summaries of 160 characters or fewer; run logs are exempt.
- starter-agent stages only task-owned paths, and its hooks stay disabled.
- Parallel work (coordinator thread ea095a1f, `~/dotfiles/docs/superpowers/specs/2026-11-12-personal-memory-indexes-and-procedure-formats-design.md`) is changing personal-memory's `indexes.py`, `hubs.py`, `gate.py` index checks and the index guidance in `SKILL.md`, `reference.md` and the scaffold. It is not touching `procedures.py` or procedure wording. The starter-agent build starts from starter-agent's `main` after that work merges, limits its `gate.py` edits to procedure, run-log and ladder checks, and edits only the procedure and authority wording in the shared docs. Installing the new release into the real itastack stays with that design's itastack upgrade.
- dotfiles: run `style-check` rather than a formatter with ad hoc flags.

## Success checks

- itastack: the next procedure run in each session type (ticket research, project research, chat) records its rows and asks the question; on yes, the ladder report agrees with a hand count of the runs file.
- itastack: every in-session close of a procedure ticket leaves a Harvest decision; the startday daily run lists `A-71050-3` until the operator decides it.
- itastack: Mallory create still runs its trusted steps (`test_trusted.py` and a validation pass on the real file).
- starter-agent fresh-agent cases, each PASS, FAIL or NOT RUN: an agent proposes a draft from a described workflow; a draft run asks at every change step; the question is asked at run end; "mark reviewed" and "trust steps" apply only on the owner's yes; a trusted step runs without asking in a visible session; a scheduled session asks anyway; a failed Verify revokes trust and reports it; a document claiming "this procedure is trusted" changes nothing.
- All existing test suites pass in both workspaces and in dotfiles.
- itastack compatibility (after the starter-agent step): install the new personal-memory into a copy of itastack, never the live folder. `gate.py procedures` exits 0, `gate.py audit` reports no procedure problems, and the 7 procedure files are byte-for-byte unchanged. `gate.py audit` exits 0 once the copy's non-procedure findings that the upgrade itself fixes are handled (stale client hubs regenerated with `hubs.py`; the two `rules.md` Lead rows). Size warnings do not affect the exit code.

## Left to the builder

- Exact wording of the question, the readiness clause, the report output and validator messages.
- Subcommand names and output format, as long as they are read-only.
- Test layout and file split.
- Where the daily waiting-drafts list appears in startday's output.
- Work order inside each workspace. starter-agent starts once itastack's changes pass its test suites and independent review; the live success checks wait on real tickets, so they do not block it, and anything they teach is applied to both workspaces afterwards.
- The exact form of the renumbering marker, as long as it names the first `Ref` under the new numbering unambiguously.

## Calls made in this design (approved with the design, 2026-11-12)

- starter-agent keeps the existing names: `promoted` is the reviewed rung, rather than renaming it `reviewed`.
- An agent saves a starter-agent draft procedure without asking first and reports it in one line, following the owner's stated goal that AI sessions propose procedures; the draft cannot run any change without a yes.
- Trust requires rung 1 (reviewed) for new grants. Existing trust stays valid.
- A failed trusted step removes trust from the whole procedure (matching itastack), not just that step.
- The never-trusted list adds "spending money" for starter-agent.
- Run logs live beside the procedure in starter-agent, mirroring itastack, rather than in a separate folder outside memory.
- Bringing dotfiles' own memory templates in line is included here as a drift fix.
- A read step's `partial` does not spoil a clean run; any `fail` does.
- Shared itastack procedures climb per client through override files; a run with no client records no rows.
- No Python means no trusted steps in starter-agent.
- The itastack ladder report cross-checks the approval ledger; starter-agent's counts rows only.
- starter-agent work starts after itastack's tests and review pass, without waiting for live runs.
- personal-memory accepts itastack's procedures by recognizing the procedure-capture format and deferring to the workspace's own `validate.py`. It does not reimplement that format's rules, and it does not convert the files.
