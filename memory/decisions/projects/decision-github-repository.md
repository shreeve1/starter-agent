---
title: Starter-agent GitHub repository
summary: This workspace uses the owner's GitHub remote, overriding local-only Git.
type: decision
status: promoted
created: 2026-10-10
updated: 2026-10-10
topics: [projects]
---

## Decision

- The owner explicitly requested pushing this project to `git@github.com:shreeve1/starter-agent.git`.
- This workspace is an exception to shipped local-only Git rules. Keep ordinary memory safety checks; never publish credentials.
- The owner supplied SSH key location `C:/Users/James/.ssh/id_ed25519_github_personal`; use it with `IdentitiesOnly=yes` for this repository. Store only the location, never key contents.

## Notes

- Source: owner's request and successful SSH remote access, 2026-10-10.
- Supersedes the no-remote clause in [Codex workspace](memory/decisions/workstation/decision-codex-workspace.md) for this workspace.
