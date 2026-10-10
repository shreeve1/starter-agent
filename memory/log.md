# Memory Log

## 2026-10-10 decision | GitHub repository exception

- Actor: agent
- Inputs: owner requested GitHub remote and push, supplied SSH key location.
- Outputs: `memory/decisions/projects/decision-github-repository.md`, superseded local-only clause in `memory/decisions/workstation/decision-codex-workspace.md`, indexes.
- Notes: saved key location only, never key contents. Shipped hooks remain disabled and unchanged.

## 2026-10-10 decision | Codex workspace with hooks skipped

- Actor: agent
- Inputs: owner requested Codex adaptation while skipping hooks.
- Outputs: `memory/decisions/workstation/decision-codex-workspace.md`, generated decision/workflow indexes, `memory/index.md`.
- Notes: hooks remain unchanged and disabled; direct audits/tests replace automatic checks. Incoming Release records and the Pristine Snapshot are preserved.
