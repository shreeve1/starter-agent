# Undoing an update

Be conservative. If anything below does not match what you see, stop, run `python .agents/skills/apply-release/scripts/apply_release.py status`, show the owner the output and ask before going on. Never hand-edit `.agents/release-state.json` or `.agents/release-backup/`.

Before `apply` changes anything, it copies the owner's current bytes of every file it will touch (committed or not) into `.agents/release-backup/<N>/`. `rollback` puts those exact bytes back. Do not undo an update with `git restore`, `git checkout` or `git revert`: they restore from the last commit and destroy edits the owner had not committed.

## Before or after `finish`

1. **Owner decision:** confirm they want to undo the whole apply of Release `<N>`.
2. `python .agents/skills/apply-release/scripts/apply_release.py rollback`. It rolls back the latest applied or unfinished Release (`--release <N>` names it explicitly; only the latest can be rolled back).
3. Show the owner the summary: `restored` (files back to their pre-apply bytes, uncommitted edits included), `deleted` (files and `.release` sidecars the apply created) and `next`.
4. If it refuses because files changed after the apply, show the owner the list. Rolling back would overwrite those changes. Only with the owner's OK, rerun with `--force`; the newer copies are saved first under `.agents/release-backup/<N>/rolled-back/`. A copy is never overwritten: if the same file is saved again with different content, the new copy gets a numbered name (`AGENTS.md.1`, `AGENTS.md.2`), so every version the owner had survives.
5. Run `git status` with the owner. The working tree is exactly as it was before the apply; their uncommitted edits are uncommitted again. The owner decides what to commit. The hooks run; never use `--no-verify`.
6. Run `status`: the applied Release is the earlier one and there is no unfinished apply.

If `rollback` is interrupted (a crash, a closed window), run `rollback` again with no arguments: it resumes that same rollback, not the earlier Release. Every pass re-checks each file, so anything the owner edited since the interruption is listed and needs `--force` (their newer copy is saved under `rolled-back/` first, as a new numbered copy if an older one is already there); files already restored are not flagged.

`rollback` never touches git history, the index or refs. After `finish` the commit `apply Release <N>` stays in history until the owner commits the restored files. The snapshot ref `refs/releases/<N>` stays; it is harmless and lets the Release be applied again later. The backup folder is kept as the owner's safety net.

## Owner without git

`rollback` works the same way without git: the backup folder is plain files. The Release's pristine files stay in `.agents/snapshots/<N>/` for reference. Run `status` afterwards and ask the owner how to proceed.
