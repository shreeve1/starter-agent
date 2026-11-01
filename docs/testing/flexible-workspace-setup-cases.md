# Flexible workspace setup checks

## Scope

Changes are limited to the starter workspace. The example bot was read only. Internal `client_*` keys and memory types remain compatible; the schema still supports one tracked-memory collection, not separate client and project hub systems at once.

## Regressions and direct probes

- Existing hub generation failed the new README/configured-folder test: the project README and design folder were absent, while an unconfigured tickets folder appeared. After the implementation, the test passes and configured folder order is retained.
- An empty `client_dirs` list previously restored hardcoded client document sections. The regression now proves no subfolder sections are added.
- Unsafe or malformed `client_dirs` values previously passed schema loading. The regression rejects paths, nonlists, nonstrings, empty names and duplicate names; project folder names and an empty list remain valid.
- Document directory/file symlinks could link outside the tracked thing. The regression now excludes those links, including a tracked root aliased to another entity.
- A real hubs.py CLI fixture under a temporary path containing spaces produces Unicode document links, passes `--check`, is byte-identical on a repeated generation, and reports drift after a new document appears.
- Existing tests cover client-default behavior and a differently named tracked collection. The proposal/research format consumer was updated to select its own formats rather than assume exactly two formats in the installed supporting-template file.

## Read-only setup scenarios

A fresh `cheap` agent (resolved to `cliproxy/deepseek-v4.1-flash`) read the original tracking model, adaptation page, folder map and schema for a no-client printing bot with two projects. It identified missing README format, inherited ticket folders, unclear procedure homes and a proof-note requirement with no empty-state fallback. Receipt: `10a4d519a7744cd788bf7c35ab5bb3df`.

A fresh same-model probe read the revised setup, tracking model, folder map and supporting templates. It selected `client_folder: projects`, suitable project document folders, owner-approved printing topic, README-only entry points without invented memory, saved tasks under `tasks/`, agent procedures under `memory/workflows/printing/`, and human runbooks with project files. It preserved schema choices on upgrade and distinguished mixed client/project work from an existing code repository. Receipt: `32ffad57d2784053addf31a914f9d3ac`.

The second probe also raised a real research-location ambiguity and old setup task-index wording. Guidance now puts project-confined research in its configured project folder, general research at root `research/`, with owner/skill paths taking precedence. Task setup now points to the existing restore-active-rows behavior. Other reported issues were expected setup choices, not contradictions: the generic schema defaults to clients until personalization, glossary headings can be created when needed, and shipped personal content still follows the existing approval-based sorting process.

## Limits

These are read-only interpretation probes, not autonomous end-to-end setup or upgrade executions. No real project, migrated notes or verified procedure was invented as proof. Native Windows/macOS, Codex and Cowork setup were not run. File-only operation is documented but was not separately exercised here. Repo-specific Python/Markdown style configuration is absent; style-check skipped those surfaces. No tools or style configuration were installed.

## Final checks

Personal-memory: 168 tests passed. Memory-setup: 6 tests passed. Hooks: 9 tests passed. Generated indexes/hubs are up to date, the memory audit passes, and git diff --check is clean. Incoming MANIFEST.json is unchanged; testy-bot retains only its pre-existing changes.

Independent read-only reviewer `cliproxy/gpt-6-luna` (receipt `6da48b642d47405d825b5ce628761819`) found one actionable issue: filenames containing spaces produced invalid Markdown destinations. The CLI regression was extended to a filename with spaces and parentheses, observed failing, then fixed by URL-encoding document destinations. The complete 168/6/9 suites and audit passed again after this fix. No other actionable review finding was reported.

Repo style configuration is absent, so no broad autoformat was applied. A separate Ruff probe found existing regex-alias/subprocess-style diagnostics in test_tasks_policy.py; those unrelated lines were left unchanged. Two existing lint findings in the already-touched hub script were fixed without changing behavior. After staging this task's exact paths, `python3 .githooks/pre-commit` passed (secret scan, memory audit and all discovered Python skill/hook test suites). Staged diff whitespace checks passed too.
