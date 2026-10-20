---
title: Codex workspace with hooks skipped
summary: Use Codex-native tools and PowerShell; leave hooks disabled and unchanged.
type: decision
status: promoted
created: 2026-10-10
updated: 2026-10-20
topics: [workstation]
---

## Decision

- The owner requested: "skip the hooks update everything else for codex".
- Keep this workspace adapted for Codex: `AGENTS.md`, `.agents/skills/`, PowerShell examples and isolated agent batches within available slots.
- Leave shipped hooks unchanged and disabled. Before each commit, stage the files and run `python .githooks/pre-commit` by hand (secret scan, memory audit, skill tests). Git pushes to the owner's GitHub remote: [GitHub repository](memory/decisions/projects/decision-github-repository.md).
- Keep `MANIFEST.json` as the incoming Release record; list local customizations under "Local changes" in `CHANGELOG.md`. Local setup guidance is `.agents/setup/CODEX.md`.
- On an update to a new Release, the shipped update steps drop `CODEX.md`, `CHANGELOG.md` and edits to `AGENTS.md`. Before the old workspace is retired, re-apply each item in its `CHANGELOG.md` "Local changes" (Codex runtime section in `AGENTS.md`, `.agents/setup/CODEX.md`, PowerShell examples and Codex tools in skills), copy that heading into the new `CHANGELOG.md`, and keep hooks disabled.

## Notes

- Source: owner's request and verified setup in this session, 2026-10-10.
