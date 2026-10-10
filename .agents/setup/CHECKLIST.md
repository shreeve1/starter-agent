# Test-system checklist

Run this once with the owner, on a scratch folder or test machine, before real use. `python` means `py -3` or `python3` if needed. Tick each box only after seeing it work.

For this Codex workspace, hook checks are not applicable: the owner chose
to leave hooks disabled and unchanged. Run audit/tests directly. Record
results only for commands actually run; see `CODEX.md` for the local checks.

## Install

- [ ] First install into an empty scratch folder by following `INSTALL.md`.
- [ ] Chosen policy verified: no `core.hooksPath` for this Codex workspace; `.githooks` only where the owner chose hooks.
- [ ] `python .agents/skills/personal-memory/gate.py --memory memory audit` exits 0.
- [ ] If hooks are enabled elsewhere: test them in a disposable workspace. If skipped here: run the memory audit and relevant tests directly; do not activate hooks for this test.
- [ ] `python .agents/skills/apply-release/scripts/apply_release.py status` shows the Release applied and one snapshot.

## Updates

- [ ] Customize one shipped file (add a line to a skill) and commit.
- [ ] Apply a second Release over it: the plan shows a merge, and after `finish` the custom line is still there.
- [ ] Conflict case: change a line the next Release also changes; `apply` exits 1, resolve with the owner (`CONFLICTS.md`), and `finish` refuses until the markers are gone.
- [ ] Rollback case: undo one apply by following `ROLLBACK.md`; `status` shows the earlier Release.

## Team edition

- [ ] (team) `.agents/operator-profile.json` exists with every key (`OPERATOR-PROFILE.md`).
- [ ] (team) Startday tests pass: `python -m unittest discover -s .agents/skills/startday/scripts/tests -q`.
- [ ] (team) The profile loads: the tests above include the profile test; a bad value stops with a clear message.

## Friends edition

- [ ] (friends) Build a start-of-day loop with `startday-spec` only if the owner wants one, and test it on a test day.

## Windows

- [ ] If hooks are enabled elsewhere: they run under Git Bash when committing from PowerShell and Git Bash. Skipped here.
- [ ] (team) `python -m pip install tzdata` done; the profile timezone loads.
- [ ] Line endings: after an update, files keep the owner's CRLF or LF style, and `plan` still reports unchanged files as unchanged.

## Harness

- [ ] The owner's agent app reads `AGENTS.md` and finds the skills (`ADAPTING.md`).
