# Adapting to the owner's harness and machine

This workspace was written for a terminal coding agent that reads `AGENTS.md` at the workspace root and loads skills from `.agents/skills/<name>/SKILL.md`. The owner may use a different desktop or terminal agent. The owner's agent works out the fit, and the owner verifies it on a test system.

## Steps

1. Find out which agent app the owner uses and how it loads instructions. Many read `AGENTS.md`; some read another file name (for example `CLAUDE.md`) or need a setting. If needed, add a short file that points at `AGENTS.md`; do not copy and fork it.
2. Find out where that app looks for skills. If it does not read `.agents/skills/`, configure it to, or link that folder to the expected place. Keep `.agents/skills/` as the real copy so updates keep working.
3. Check the tools the skills call exist: `git`, Python (`python`, `py -3` or `python3`), and on Windows Git Bash for the hooks.
4. Check the hooks run: `git config core.hooksPath` prints `.githooks`.
5. Note anything that does not fit (a command the app lacks, a path that differs) and show the owner before changing shipped files. Changes to shipped files are kept across updates but may conflict later.
6. Run `CHECKLIST.md` on a test system. Do not treat any of this as working until the owner has run it.

## Start-of-day loop

- (friends) There is no ready-made `startday`. The `startday-spec` skill is a recipe: run it with the owner through `talk-it-through` to build the owner's own loop.
- (team) `startday` ships and reads the Operator Profile (`OPERATOR-PROFILE.md`). Its loop command, watcher, notifications and transcript paths were written for one particular harness and machine; its adaptation notes are in the skill.

How the loop runs under another harness is for the owner's agent to work out and for the owner to verify on a test system. It is not designed here.
