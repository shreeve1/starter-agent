# Applying a later Release

The full procedure, commands and exit codes are in `.agents/skills/apply-release/SKILL.md`. This page is the short loop plus how each tricky case is handled. `python` means `py -3` or `python3` if needed.

## The loop

1. `python .agents/skills/apply-release/scripts/apply_release.py status`. If an apply is unfinished, rerun `apply` with the same folder first.
2. Read the Release's `CHANGELOG.md`; check the folder is intact (`MANIFEST.md`).
3. `python .agents/skills/apply-release/scripts/apply_release.py plan <release folder>`. Read-only.
4. **Owner decision:** talk the plan through in plain words: what is new, what merges into files the owner changed, every conflict, report, schema hold and blocking dirty file. No explicit OK, no apply.
5. `python .agents/skills/apply-release/scripts/apply_release.py apply <release folder>`.
6. **Owner decisions:** resolve each conflict with the owner, one file at a time (`CONFLICTS.md`).
7. (team) If the Release added client notes, run `python .agents/skills/personal-memory/hubs.py` so each new note is listed on its hub, then `python .agents/skills/personal-memory/gate.py --memory memory audit`; it prints any page still missing from `memory/index.md`, so add a row for each. Without this the commit hook's audit fails.
8. `python .agents/skills/apply-release/scripts/apply_release.py finish`. It snapshots and commits `apply Release <N>`.

## Cases

**Owner deleted a file.** It stays deleted. If the Release changed that file, you get a conflict showing only the Release side (binary: a `.release` sidecar). Ask the owner; to keep it deleted, delete the file.

**Owner renamed a file.** Treated as the owner deleting the old file and creating a new one of their own. The rules above apply to the old name; the new name is left alone.

**Release deletes a file.** Deleted only if the owner never changed it. If the owner changed it, it is kept and reported (`release-removed-owner-modified`); ask the owner whether to keep it.

**Release renames a file.** Handled as a delete of the old path plus a new file at the new path, each by the rules here.

**New Release file where the owner already has a file.** Conflict `collision` with two-way markers; the owner's file is never overwritten. Resolve with the owner.

**Skipped Releases (for example 1 straight to 3).** Fine. The merge uses the latest applied snapshot as the base.

**Interrupted apply.** `status` shows the unfinished apply. Rerun `apply` with the same Release folder; it is safe to rerun. A different Release is refused until this one is finished or rolled back.

**Dirty tree.** `apply` refuses if uncommitted or untracked files exist that the plan does not touch cleanly; `plan` lists them under `dirty_blocking`. Ask the owner to commit or set them aside. Use `--allow-dirty` only with the owner's OK. `finish` never stages them.

**Owner without git.** `plan`, `apply` and `finish` still work; snapshots go to `.agents/snapshots/<N>/` and nothing is committed. Text merges still need Git installed (`git merge-file`), so install Git anyway.

**Binary files.** Never merged. The Release copy is taken only if the owner's copy is unchanged; otherwise a conflict with a `<path>.release` sidecar.

**File mode changes.** Applied on macOS/Linux, ignored on Windows.

**Snapshot growth.** One snapshot per applied Release; nothing is pruned automatically. `status` reports the count. Removing old snapshots: see SKILL.md, and ask the owner first.

**A Release changes a file's class.** A path that was `seed` or `local` and that the owner deleted stays deleted even when it becomes `merge` (reported as `owner-deleted` with `class_change`). If the file still exists, it merges normally from now on.

**A seed note the owner deleted.** Never comes back. Seeds are installed once and never touched or restored.

**Schema changes.** `memory/schema.json` is merged as data. A removal still used by notes is held; see `CONFLICTS.md`.

**Release for the other edition, or not newer.** Refused; nothing written.

## Changed your mind

See `ROLLBACK.md`: `apply_release.py rollback` restores the exact pre-apply files, before or after `finish`, including edits the owner had not committed.
