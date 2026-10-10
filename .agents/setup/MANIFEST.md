# MANIFEST.json

Every Release has `MANIFEST.json` at its root. It holds:

- `edition`: `friends` or `team`.
- `release`: the Release number (whole number, higher is newer).
- For each file path: its `class` (`merge`, `seed` or `local`), its `sha256` (computed over the file with line endings turned into LF, so Windows CRLF copies still match), and its `mode`.

## What each class means for updates

- `merge`: shared files (skills, `AGENTS.md`, hooks, these docs). Updated by a 3-way merge, so the owner's changes are kept and the Release's changes come in. If both changed the same lines, it is a conflict for the owner to decide.
- `seed`: starter notes. Installed once if missing, then the owner's. Never changed again, never restored after the owner deletes them.
- `local`: the owner's own files (for example `memory/index.md`, the Operator Profile). Installed once if missing, never touched.

Details: `.agents/skills/apply-release/SKILL.md`.

## Checking a Release folder is intact

1. The folder has `MANIFEST.json` and `CHANGELOG.md` at its root.
2. `edition` matches the workspace (`status` shows the applied edition) and `release` is higher than the one applied.
3. Run `python .agents/skills/apply-release/scripts/apply_release.py plan <release folder>`. Before planning it checks every file listed in the manifest exists and matches its `sha256`. A missing or damaged file is refused with a message naming the file; nothing is written. Ask the owner for a fresh copy of the Release.

Never edit `MANIFEST.json` to make a check pass.
