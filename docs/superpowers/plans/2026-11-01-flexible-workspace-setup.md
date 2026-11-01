# Flexible Workspace Setup Implementation Plan

**Goal:** Personalize a starter for client work, independent projects, or another recurring subject without inheriting irrelevant client folders.

**Approved description:** The owner's approval in this conversation covers purpose-led setup, a project README format, separate project/task/memory/procedure homes, configurable document discovery, upgrade preservation, and one real setup proof. Keep internal `client_*` names compatible. Change only the starter; use testy-bot read-only.

**Architecture:** Keep the existing schema and memory layout. Setup chooses the tracked folder, document subfolders, subjects and workflow topics together. Hubs read configured document folders and an optional root README, only within the workspace and tracked subject. No new service, dependency or live-system change.

## Checks

- Client defaults and existing notes continue to work.
- Project README and configured subfolders appear in generated hubs; unconfigured folders do not.
- Invalid document-folder names and escaping links cannot introduce outside content.
- Projects with no durable memory remain discoverable through project READMEs and the folder map; no fictional proof note.
- Upgrades preserve owner topics, document folders, projects and task history.
- File-only setup describes manual checks without claiming automated verification.

## Implementation

- [x] Add failing hub tests for configured folders, README discovery, empty folders and escaping links; schema tests for safe document-folder values.
- [x] Make hub generation honor `client_dirs` and include an existing README; validate configured folder names and keep reads inside the intended subject.
- [x] Update tracking-model and setup/upgrade guidance; add a copyable project README to installed supporting templates and route project requests to it.
- [x] Update the folder map and memory contract after verified recovery snapshots. Keep procedures authoritative only after real verification and approval.
- [x] Run memory/setup/hook tests, real CLI fixture checks and a fresh read-only review. Record setup scenario evidence and limits, run the pre-commit checks, and commit only this task's files.

## Verification

168 personal-memory tests, 6 setup tests and 9 hook tests pass. Index/hub checks and memory audit pass. Fresh read-only setup probes and an independent reviewer are recorded in `docs/testing/flexible-workspace-setup-cases.md`; the reviewer's filename-space issue was reproduced and fixed. No end-to-end setup/upgrade or native-client test is claimed.

## Execution decisions

Work in the clean starter checkout, as approved, after coordinating ownership with the other session. Preserve `MANIFEST.json` as the incoming Release record. Do not scaffold fake projects in the starter or change the example bot.
