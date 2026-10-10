# Resolving conflicts

A conflict means the owner and the Release both changed the same part of a file. The agent never decides alone.

## What markers look like

Shown indented here on purpose: a line that starts at the left edge with these markers would count as an unresolved conflict.

        <<<<<<< owner
        the owner's version of these lines
        =======
        the Release's version of these lines
        >>>>>>> release 4

A 3-way conflict may also show a `||||||| snapshot` section with the previous Release's text. A file the owner deleted shows `owner (you deleted this file)` with an empty owner side.

## How to resolve, file by file, WITH the owner

1. List the conflicted files from the `apply` output or `status`.
2. For one file at a time, explain both sides in plain words: what the owner had, what the Release brings, and why it might matter.
3. Ask which to keep, or how to combine them. Never guess; if the owner is unsure, leave it and come back.
4. Edit the file to the chosen result and remove every marker line.
5. Move to the next file.

## Binary files and sidecars

A binary file (or a file the owner deleted that the Release changed) gets a `<path>.release` sidecar holding the Release copy. Ask the owner which to keep. Put the chosen content at `<path>` (or delete it) and delete the sidecar.

## Held schema changes

If a Release removes or renames an entry in `memory/schema.json` that the owner's notes still use, the change is held and the notes are listed. With the owner, move each listed note to the new entry first. Then run `python .agents/skills/apply-release/scripts/apply_release.py resolve-hold <entry>` (use `<key>:<entry>` if asked). Exit 1 lists notes that still use it.

## Finishing

`finish` refuses while any marker line, sidecar or held schema change remains. Fix what it names, then run it again.

Details: `.agents/skills/apply-release/SKILL.md`.
