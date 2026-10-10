# Setup

This folder holds the instructions for installing and updating this workspace. It is written for the owner's agent to follow, with the owner deciding at every marked point.

## What an edition is

An edition is a ready-made copy of an agent workspace: instructions (`AGENTS.md`), skills under `.agents/skills/`, a memory folder and git hooks. There are two editions, friends and team. Steps marked `(team)` apply only to the team edition; steps marked `(friends)` only to the friends edition.

A Release is one version of an edition, delivered as a plain folder. Its root holds `MANIFEST.json` (what each file is) and `CHANGELOG.md` (what changed).

## The flow in one sentence

The owner's agent runs the `apply-release` skill: it plans the update, talks it through with the owner, applies it, resolves any conflicts with the owner, and finishes with a snapshot and a commit.

The commands, plan, state file and exit codes are described in `.agents/skills/apply-release/SKILL.md`. These documents point at it; they do not replace it.

## Which document to open

- First time on this machine: `INSTALL.md`.
- (team) Filling in who the owner is: `OPERATOR-PROFILE.md`.
- A new Release arrived: `UPDATE.md`.
- The update stopped with conflicts: `CONFLICTS.md`.
- The owner wants to undo an update: `ROLLBACK.md`.
- Checking what is inside a Release: `MANIFEST.md`.
- Found a stray `<!-- edition:... -->` line: `MARKERS.md`.
- Making it work with the owner's own agent app and computer: `ADAPTING.md`.
- Using Codex on Windows, with hooks skipped: `CODEX.md`.
- Proving it all works on a test system: `CHECKLIST.md`.

## Ground rules for the agent

- Never apply anything without the owner's explicit OK.
- Never guess in a conflict; show both sides and ask.
- Never skip the git hooks (`--no-verify`).
- Try everything on a test system first (`CHECKLIST.md`).
