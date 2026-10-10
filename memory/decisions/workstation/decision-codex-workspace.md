---
title: Codex workspace with hooks skipped
summary: Use Codex-native tools and PowerShell; leave hooks disabled and unchanged.
type: decision
status: promoted
created: 2026-10-10
updated: 2026-10-10
topics: [workstation]
---

## Decision

- The owner requested: "skip the hooks update everything else for codex".
- Keep this workspace adapted for Codex: `AGENTS.md`, `.agents/skills/`, PowerShell examples and isolated agent batches within available slots.
- Leave shipped hooks unchanged and disabled. Run audits and relevant tests directly before local commits; keep Git without remotes.
- Preserve incoming Release records and the original Pristine Snapshot when making local customizations. Local setup guidance is `.agents/setup/CODEX.md`.

## Notes

- Source: owner's request and verified setup in this session, 2026-10-10.
