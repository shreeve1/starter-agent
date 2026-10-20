# Codex setup

Open this folder as a local Codex project. Project instructions stay in
`AGENTS.md`; skills stay in `.agents/skills/`. No copied `CLAUDE.md`, skill
symlink or companion CLI is needed.

## Local configuration

- Windows shell: PowerShell. Use the available file/shell tools and `rg`.
- Python: verify `python --version`; generic `python3` commands also work
  where that name exists. Do not assume a `py` launcher.
- Git: this workspace pushes to the owner's GitHub remote
  (`memory/decisions/projects/decision-github-repository.md`). Shipped hooks
  stay unchanged and disabled at the owner's request. Do not set
  `core.hooksPath` or bypass hooks. Run checks directly before commits.
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

This workspace follows friends Edition Release 5 (`MANIFEST.json`). Updates
work as `README.md` "A newer version arrived" describes: a fresh copy of the
new Release with this workspace's content brought across. Local Codex
adaptations and owner changes are listed under "Local changes" in
`CHANGELOG.md`; carry them across with the update.

## Checks

Run from the workspace root in PowerShell:

```powershell
git rev-parse --show-toplevel
git config --show-origin --get core.hooksPath
python .agents/skills/personal-memory/gate.py --memory memory audit
python -m unittest discover -s .agents/skills/personal-memory/tests -q
python -m unittest discover -s .agents/skills/startday-spec/scripts/tests -q
python -m unittest discover -s .githooks/tests -q
git diff --check
```

Expected: this workspace is the Git root; hooksPath is empty; audit and
tests exit 0. A later, deliberately configured hook changes that
expectation; inspect it instead of overwriting it.

After skill edits, Codex normally rediscovers them; reopen the chat/app if
the selector remains stale. Exercise a real task before calling any skill
fully verified. Optional yt-dlp, uv or Playwright installation is separate
from this setup and requires the owner's approval.
