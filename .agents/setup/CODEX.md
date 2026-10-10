# Codex setup

Open this folder as a local Codex project. Project instructions stay in
`AGENTS.md`; skills stay in `.agents/skills/`. No copied `CLAUDE.md`, skill
symlink or companion CLI is needed.

## Local configuration

- Windows shell: PowerShell. Use the available file/shell tools and `rg`.
- Python: verify `python --version`; this machine has Python 3.14. Generic
  `python3` commands also work here. On another machine verify the executable
  first; do not assume a `py` launcher.
- Git: local history only, no remotes. Shipped hooks remain unchanged and
  disabled at the owner's request. Do not set `core.hooksPath` or bypass hooks.
  Run checks directly before commits.
- Delegation: use Codex collaboration tools only when the task or skill
  calls for it. Respect the current slot limit; independent fresh-context
  branches may run in batches. Keep internal subtasks in the current chat.
- Research: use built-in web search/open tools. Interactive previews use
  the available browser integration; native desktop control is optional.
- Scheduled work: only when the owner requests it, use Codex's automation
  tools. Prefer a thread heartbeat for follow-up work in the same chat;
  keep unchanged-state runs quiet. Do not build a shell scheduler merely
  because a Bash example exists.
- Teaching: preserve `teach/agents/openai.yaml`'s explicit-only policy.

## Release baseline

The original friends Edition Release 1 was validated against its Manifest,
installed in a temporary empty Git workspace using `apply-release`, and
its Git history and generated state adopted here before local edits.
`refs/releases/1` holds that untouched Pristine Snapshot. Local edits are
owner customizations, not a new Release: do not regenerate `MANIFEST.json`
or `CHANGELOG.md` to hide those differences. Later Releases follow the
normal `apply-release` plan, approval and merge flow.

## Checks

Run from the workspace root in PowerShell:

```powershell
git rev-parse --show-toplevel
git remote -v
git config --show-origin --get core.hooksPath
python .agents/skills/apply-release/scripts/apply_release.py status
python .agents/skills/personal-memory/gate.py --memory memory audit
python -m unittest discover -s .agents/skills/personal-memory/tests -q
python -m unittest discover -s .agents/skills/apply-release/tests -q
git diff --check
```

Expected: this workspace is the Git root; remote and hooksPath outputs are
empty; Release status shows friends, Release 1, a Git snapshot and no
unfinished apply; audit and tests exit 0. A later, deliberately configured
hook or remote changes those expectations—inspect instead of overwriting it.

After skill edits, Codex normally rediscovers them; reopen the chat/app if
the selector remains stale. Exercise a real task before calling any skill
fully verified. Optional yt-dlp, uv or Playwright installation is separate
from this setup and requires the owner's approval.

## Verified 2026-10-10

- Memory audit passed. Memory tests: 17 passed. Release tests: 46 passed,
  two Windows-inapplicable file-mode tests skipped.
- All 13 PowerShell blocks in skill entry points parsed successfully.
- The Excalidraw PowerShell background-server example served its preview
  over localhost and the test process was stopped.
- YouTube metadata parsing and literal-path moves handled bracketed file
  names in local fixtures; no video was downloaded. Ignored smoke fixtures
  remain under `tmp/` and `youtube/**/raw/`.
- All six shipped hook files matched their original Manifest hashes.
  Git had no hooksPath or remotes; Release status showed one Git snapshot.
- Optional package installs, a real YouTube pull, PNG rendering and full
  teaching/brainstorming workflows were not exercised.
