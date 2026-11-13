---
name: memory-audit
description: Audit and maintain a project's agent instructions and memory, with a focused approval batch for deletions and global-instruction changes.
disable-model-invocation: true
---

# Memory Audit

Run only when the owner invokes this skill. It audits the project's instructions and memory, applies pre-approved non-deleting fixes, and reports decisions that still need the owner.

## Run

1. **Scope.** Read the project's `AGENTS.md`/`CLAUDE.md`, `memory/README.md`, `memory/rules.md`, indexes, and every file the instruction chain says to load. Read the `writing-for-agents` skill (`SKILL.md` and `SKILL-MECHANICS.md`) before any edit. Use the copy the project's AGENTS.md names for `personal-memory`; when that is a project-local copy, compare it with the shared `~/.agents/skills/personal-memory` and list an older copy under **Unresolved** with the behaviour it lacks, as a recommended update for the owner. If the project has no `memory/` or `memory/rules.md`, stop and point to `memory-setup`. Note whether the project is a git repo. In a git project, follow its git instructions, including pull-before-work and rules for other people's uncommitted changes; ask the owner and leave any file with uncommitted changes he says to ask about untouched. Without git, edit in place: the project's own undo (such as Syncthing versions) is the way back, so record every changed path for the report. **Complete when** the instruction chain and applicable project rules are read, or the setup stop is reported.

2. **Baseline.** Run the checks the project's `personal-memory` copy supports: `gate.py --memory memory audit`, `gate.py procedures`, `gate.py stale`, `gate.py links`, and relevant project tests. Read all warnings and failures; record the initial results. Use `indexes.py` after memory workflow or decision edits. **Complete when** each requested check has a recorded result, or its absence is recorded as unresolved.

3. **Steering.** Review the project's `AGENTS.md`/`CLAUDE.md`, all of `memory/`, `CONTEXT.md`, and every file a `rules.md` row or startup instruction tells agents to load. Check each trigger, instruction, and pointer against its target and `personal-memory`; note contradictions, duplicated meanings, stale directions, wrong file types, and instructions without an applicable trigger. Other linked files are read-only evidence for whether a pointer resolves and says what its instruction claims. **Complete when** every in-boundary instruction and pointer has been checked.

4. **Stale facts.** Review memory notes flagged by `gate.py stale`, any note edited for another reason, and every fact a deletion candidate calls obsolete. Verify each claim at its source with read-only checks: repository and project fact files first, then the live systems the project works with, following its own access and lookup-order rules: its connectors in a client workspace (such as ITAStack's), its observability stack and then SSH in an infrastructure repo (such as homelab). Read-only means list, get, show, status, logs and queries; never create, update, restart, send, approve or delete anything, and never open a credential record. Correct a fact a live check contradicts (a fix), and update a note's `verified` or `updated` date only when you checked its claims that day; never invent dates. A fact you cannot check read-only, or whose system is unreachable, stays unchanged under **Unresolved** with the reason. Record each live check (system, command or operation, result) under **Review**. Fact files are evidence, not audit targets. **Complete when** each stale, edited or deletion-candidate fact is verified, corrected, or reported unresolved with its reason.

5. **Size.** Review every `gate.py audit` size, summary, history, link, and index warning inside the audit boundary, including the `CONTEXT.md` limit, whether or not the run touched that file. Keep each note within 6144 bytes, summaries within 160 characters, and `CONTEXT.md` within 24576 bytes. Shrink first by proposing deletions (step 6); move only content agents still need. **Complete when** every in-boundary warning is resolved, covered by a proposed deletion with its byte saving stated, or listed under **Unresolved**.

6. **Fix and find deletions.** Apply `writing-for-agents`: keep one source of truth, use sharp pointers, and word triggers for when content is needed. Non-deleting changes inside this audit boundary—including project `AGENTS.md`/`CLAUDE.md`—are pre-approved fixes; correct wrong facts with evidence and retain their meaning. Memory edits follow `personal-memory` (frontmatter, index rows, `indexes.py`). Correcting a wrong fact or a contradicted instruction to what the evidence supports is a fix; a deletion removes content whose meaning goes away with no replacement. Removing a `memory/index.md` row that a generated index (topic or hub index) already lists is a fix: the entry stays reachable there. Actively hunt deletion candidates: wrong or obsolete content, duplicates, no-ops, unused exposition, sediment, and notes about things that are gone. Propose each deletion candidate where it sits; never move it to a new file first. Keep every line that is still true or still ahead (a future date, an open item, a live warning, a recovery step): delete history, not current facts. Relocate only material agents still need. Each candidate names exact lines or files, never an open-ended "optional trim". Skills are report-only. Procedure steps (`type: procedure` files) are owner-approved: any change to them goes in the approval batch, never in as a fix. For every deletion candidate, gather its evidence and `gate.py backlinks <path>` result. **Complete when** every non-deleting fix is applied or each proposed deletion has evidence and backlinks recorded.

7. **Verify and record.** Re-run the step 2 checks. Resolve warnings on changed files; list procedure failures and other unresolved findings. In a git project, commit by kind—Steering, Stale facts, Size—with every changed path and reason in the commit body, and push verified commits without asking; no force pushes. Without git, list every changed path and reason by kind under **Changed files** in the report. **Complete when** checks and commits or the changed-file list are recorded and touched-file warnings are clear or reported unresolved.

8. **Report and ask.** Give counts fixed by kind and commit hashes or **Changed files**. Include **Review** (each changed rule, decision, preference, procedure, or project instruction, with reason), **Unresolved** (unverifiable facts, procedures needing real approval or verification, and skill conflicts), and one final **For approval** batch. The batch gives every proposed deletion's target, reason, evidence, and backlinks, plus every recommended global-instruction change's exact text and the conflict it resolves. Changes to global instructions, including `.agents/AGENTS.md`, need the owner's yes. The owner may approve all, some, or none. **Complete when** the report and single approval batch are delivered.

9. **Apply approvals.** Apply only what the owner approves; repair pointers orphaned by approved deletions. Re-run verification from step 7, then commit deletions and global-instruction changes separately and push, or list them under **Changed files** without git. Leave declined or unanswered candidates untouched and list them once in the closing report. **Complete when** every finding is fixed, approved and applied, declined, or listed under **Unresolved** with its reason.

## Authority

This skill's non-deleting changes within its audit boundary and its pushes are pre-approved; the owner reviews the changes afterwards. Deletions, procedure-step changes and global-instruction changes wait for the owner's yes. Read-only checks of live systems and connectors are pre-approved; changing a live system is outside this skill. Skills are report-only. Follow project rules for other people's uncommitted changes. Make no force push, never invent dates, and omit credentials.

## Audit boundary

- **Steering:** project `AGENTS.md`/`CLAUDE.md`, `memory/`, `CONTEXT.md`, and files named by `rules.md` or startup instructions. Other linked material is read-only evidence.
- **Stale facts:** stale-flagged and otherwise-edited memory notes only; project fact files are evidence, not targets.
- **Size:** issues reported by `gate.py audit`.

## Review Focus

- For someone's uncommitted changes in a file this run would edit, follow project policy: ask the owner and leave that file alone.
- Before proposing a deletion, inspect its backlinks; include them in the approval batch and repair orphaned pointers only after approval.
- When the owner declines or does not answer, delete nothing; retain ordinary fixes and list declined items once.
- Use the copy the project's AGENTS.md names for `personal-memory`.
- When `memory/` or `memory/rules.md` is missing, stop and point to `memory-setup`.
