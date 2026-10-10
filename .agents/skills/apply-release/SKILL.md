---
name: apply-release
description: Apply a new Release of this workspace (a plain folder the owner received from whoever maintains the edition) without losing the owner's own changes. Plans the update, talks it through with the owner, 3-way merges against the Pristine Snapshot, resolves conflicts with the owner, then snapshots and commits. Use for "apply the new release", "update my workspace", "I got a new version", or when `.agents/release-state.json` shows an unfinished apply.
---

# apply-release

A Release is a plain folder the owner received from whoever maintains the edition: the whole edition tree plus `MANIFEST.json` and `CHANGELOG.md` at its root. This skill brings the owner's workspace up to that Release and keeps every change the owner made. Vocabulary (Release, Manifest, Seed, Pristine Snapshot, Schema) is in `CONTEXT.md`.

Run every command from the workspace root:

```
python .agents/skills/apply-release/scripts/apply_release.py <command> [args] [--root <workspace>]
```

## Steps

1. `status`. If `in_progress` is set, a previous apply was interrupted: rerun `apply` with the same Release folder (it is safe to rerun), then continue at step 5.
2. Read the Release's `CHANGELOG.md`. Run `plan <release_dir>`. It changes nothing.
3. Talk the plan through with the owner in plain language: what is new, what will be merged into files they changed, every entry in `conflicts`, `reports` and `schema.held`, and any `dirty_blocking` files. Get an explicit OK before going on. No OK, no `apply`.
4. `apply <release_dir>`. Exit 0: go to step 6. Exit 1: conflicts or schema holds remain. Exit 2: refused (message says why; nothing was written).
5. Resolve WITH the owner, one file at a time. Show both sides, ask which to keep or how to combine, edit the file, remove every marker line. For a `<path>.release` sidecar (binary file, or owner-deleted file the Release changed): the owner picks, you put the chosen content at `<path>` (or delete it) and delete the sidecar. For each schema hold: help the owner move the listed notes to the new entry, then `resolve-hold <entry>`.
6. `finish`. It refuses while conflicts or holds remain. It stores the Pristine Snapshot and commits `apply Release <N>`. The commit hook runs normally; if it fails, fix what it reports and commit with the same message. Never use `--no-verify`.

If the owner changes their mind at any point, follow `.agents/setup/ROLLBACK.md`.

## Commands

| Command | Does | Exit |
| --- | --- | --- |
| `plan <release_dir>` | Prints the JSON plan. Strictly read-only: no file, index or ref changes. | 0, 2 refused |
| `apply <release_dir> [--allow-dirty]` | Writes the plan into the working tree, with conflict markers where needed. Never commits. Idempotent: rerun after an interruption. | 0 clean, 1 conflicts/holds left, 2 refused |
| `finish` | Refuses while conflicts or holds remain. Stores the snapshot, updates state, commits. | 0, 1 refused or hook failed, 2 nothing to finish |
| `status` | Applied Release, unfinished apply (planned/done/pending files), conflicts, holds, snapshot count. | 0 |
| `resolve-hold <entry>` | Re-checks that no note uses the held schema entry; if none, removes it from `memory/schema.json` and clears the hold. Use `<key>:<entry>` when the name is held under two keys. | 0 cleared, 1 still used (lists notes) |
| `rollback [--release N] [--force]` | Before or after `finish`, restores every file the apply touched to its exact pre-apply bytes from `.agents/release-backup/<N>/` (copied before the first write; uncommitted edits included), deletes files it created, restores the state file. Never touches git history, index or refs. Refuses files changed since the apply unless `--force` (newer copies saved to `rolled-back/`, never overwritten: a different version of the same file gets a numbered copy). See `.agents/setup/ROLLBACK.md`. | 0, 2 refused |

## Rules

- **Pristine Snapshot.** `finish` stores the exact Release tree. In a git repo: commit built with plumbing, kept at `refs/releases/<N>` (survives `git gc`; only trees, no history chain). Without git: a copy at `.agents/snapshots/<N>/`. Nothing is pruned automatically; `status` reports the count.
- **Merge base.** Base is always the previous snapshot's file, ours the owner's file, theirs the Release file (`git merge-file`). Skipped Releases (1 -> 3) merge against the latest applied snapshot. Hashes compare LF-normalized bytes; the owner's CRLF style is kept when writing.
- **Classes** (from `MANIFEST.json`):
  - `merge`: 3-way merged. Owner unchanged -> take the Release. Release unchanged -> keep owner.
  - `seed`: installed once if absent; never touched again, never restored after the owner deletes it.
  - `local`: the owner's file (Operator Profile, `memory/index.md`); installed once if absent, never touched.
  - Class change: a path once `seed` or `local` that the owner deleted stays deleted even when it becomes `merge` (`reason: owner-deleted`, `class_change: "seed->merge"`). A path that existed as seed/local and is now `merge` merges normally.
- **Update cases.**
  - Owner deleted a `merge` file: stays deleted; if the Release changed it, conflict (text: a file with only the Release side in markers; binary: `.release` sidecar). Delete the file to keep it deleted.
  - Owner renamed a file: treated as delete + new file of the owner's.
  - Release deleted a file: deleted only if the owner copy equals the snapshot, else kept and reported (`release-removed-owner-modified`).
  - Release renamed a file: delete + add.
  - New Release file at a path the owner already has (also any existing `merge` file on first install): conflict `collision`, two-way markers, never overwritten.
  - Binary files are never merged: Release taken only if the owner copy equals the snapshot, else conflict with `<path>.release` sidecar.
  - `mode` applied on POSIX, ignored on Windows.
- **Dirty tree.** `apply` refuses if uncommitted or untracked files exist other than ones the plan touches cleanly (`add`, `update`, `merge`, `delete`, `schema`); `plan.dirty_blocking` lists them. Ask the owner to commit or set them aside; `--allow-dirty` only with the owner's OK. `finish` never stages them.
- **Schema** (`memory/schema.json`) is merged as data, never as text: owner entries kept, Release additions appended. A Release removal applies only if no note uses the entry (client subject: any `memory/clients/<subject>/**/*.md` or a frontmatter `subject: <subject>`; topic: any `.md` under `memory/<topic_dir>/<topic>/`). Otherwise it is held: kept in the file, listed in `plan.schema.held` with the notes, stored in state `holds`. A rename is a removal plus an addition, so the old name is held the same way.
- **Conflicts.** `finish` refuses while any conflicted file still has a marker line (`<<<<<<< `, `>>>>>>> `), a sidecar remains, or any workspace file has all three markers.
- **Commit.** `finish` commits `apply Release <N>` with only the applied files and the state file, and only if nothing unrelated is staged (otherwise it reports `commit_skipped` and the owner commits). No repo: state only.
- **No git installed:** `plan`, `apply` and `finish` still work with folder snapshots; text merges need `git merge-file`, so install Git first.

## State: `.agents/release-state.json`

```json
{
  "version": 1,
  "edition": "friends",
  "release": 2,
  "snapshots": {"1": {"store": "git", "location": "refs/releases/1"},
                "2": {"store": "folder", "location": ".agents/snapshots/2"}},
  "seeds_installed": ["memory/guides/welcome.md"],
  "locals_installed": [".agents/operator-profile.json", "memory/index.md"],
  "holds": [{"key": "client_subjects", "entry": "halo", "change": "remove", "release": 3,
             "notes": ["memory/clients/halo/acme/note.md"]}],
  "in_progress": null,
  "history": [{"release": 2, "started": "2026-10-09T10:00:00+00:00", "finished": "2026-10-09T10:20:00+00:00"}]
}
```

While an apply runs, `in_progress` is `{"release", "edition", "release_dir", "started", "files": [{"path", "action", "target": "<sha256 of planned content or null>"}], "done": [paths], "conflicts": [plan conflicts]}`. Do not edit this file by hand.

## Plan JSON

```json
{
  "edition": "friends", "release": 3, "from_release": 1, "first_install": false, "git_repo": true,
  "files": [{"path": "AGENTS.md", "class": "merge", "action": "merge", "reason": "clean-3-way", "mode": "644"}],
  "conflicts": [{"path": "README.md", "kind": "overlap"},
                {"path": "assets/logo.png", "kind": "binary", "sidecar": "assets/logo.png.release"}],
  "reports": [{"path": "memory/guides/tips.md", "reason": "owner-deleted", "class_change": "seed->merge"}],
  "schema": {"added": {"client_subjects": ["network"]}, "removed": {"topics": ["skills"]},
             "held": [{"key": "client_subjects", "entry": "halo", "change": "remove", "release": 3, "notes": ["..."]}],
             "holds_cleared": []},
  "holds_pending": [],
  "dirty_blocking": []
}
```

- `action`: `add`, `update` (owner unchanged, take Release), `merge` (clean 3-way), `conflict`, `delete`, `keep`, `schema`.
- `reason`: `new`, `install-once`, `owner-unchanged`, `clean-3-way`, `same`, `unchanged-in-release`, `owner-file`, `owner-deleted`, `already-absent`, `release-removed`, `release-removed-owner-modified`, `collision`, `overlap`, `binary`, `owner-deleted-release-changed`, `schema-data-merge`, `schema-unchanged`, `schema-restored`.
- `conflicts[].kind`: `overlap`, `collision`, `binary`, `owner-deleted-release-changed`.
- `class_change` appears on a file entry when the class differs from the previous Release; `mode` when the file is written or its mode changed.
