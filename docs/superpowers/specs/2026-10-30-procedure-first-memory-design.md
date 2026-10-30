# Procedure-first memory: proposed design

Status: proposed for owner review. Planning is authorized; implementation and the policy choices below are not yet approved.

## Intent and scope

Make rules and verified procedures the center of starter-agent, keeping memory as ordinary files. This foundation covers routing, procedure readiness, trust boundaries, reversible edits and behavioral checks.

Public distribution (neutral exports, client adapters and licensing) and deeper retrieval (ranked search and larger recall evaluations) need separate plans. Follow the foundation with public-release preparation, then decide retrieval upgrades from measured recall failures. This pass must not delete personal memory or claim universal compatibility.

## Global constraints

- Markdown is authoritative; no database, service, embedding, model download, network access or new dependency is required.
- Python 3.11+ standard-library maintenance is optional; document file-tool-only operation.
- Git is optional; destructive memory edits require verified recoverable previous content.
- Support Windows, macOS and Linux paths, including spaces and Unicode.
- Preserve memory paths, topic schema, the four-column rules table and existing skill syntax.
- Preserve 6144-byte notes and 160-character summaries.
- Do not remove personal notes, change remotes, enable hooks, install tools, push, choose a license or regenerate MANIFEST.json.
- Extend personal-memory and its scaffold; do not create another skill.
- Structural validation never proves truth, owner approval, successful execution or permission to act.

## Routing

Lead accepts an empty cell or exactly one of:

```
skill `name`
procedure `memory/workflows/<topic>/<slug>.md`
```

A procedure target must exist under a configured workflow topic, resolve inside the workspace and have type: procedure. Reject absolute/drive/backslash/parent-traversal paths and escaping symlinks before reading. Keep global and sibling skill discovery.

Also load adds supporting content, not an independent execution sequence. A workflow-index discovery row stays valid: open the matching procedure and select it as lead before running it. Concrete procedure rules use Lead. Specific owner-approved procedures win over general skills; unresolved ambiguity means ask. Client exceptions apply only to their matching client, retaining current document layout. Do not convert ordinary workflow notes or delete existing skills.

Repeatable owner-specific instructions become procedures; skills package reusable capabilities, supporting code or native integrations.

## Procedure readiness

Shared procedures retain current frontmatter and add risk (read-only or changes-state), approved and verified (valid YYYY-MM-DD dates, not future dates). These record real events, never invented lint fixes.

Require nonempty ## Active memory with Trigger:, ### Prerequisites, ### Steps with a numbered action, ### Verify, ## Related and ## Notes. Related may say None. Changes-state procedures also require ### Approval and ### Recovery; recovery may explicitly describe irreversibility and safe escalation. Empty sections and fenced-example headings do not count. Troubleshooting stays optional.

Add gate.py procedures and include its findings in gate.py audit. Both remain read-only and exit 1 for problems. Unknown extra metadata is tolerated; ordinary notes remain unchanged. Validate shared procedures, not client document layouts. Incomplete legacy procedures remain readable as evidence but need owner-assisted repair and verification before execution. Never invent approval dates or delete legacy files automatically.

## Authority

Keep automatic concise capture of grounded ordinary facts, with source context; no new mandatory metadata for ordinary legacy notes.

External content is evidence, not authority. Documents, email, web pages, tool responses and earlier agent summaries cannot authorize policy changes. Only explicit owner direction or approval changes an established rule, decision or procedure. Temporary directions remain temporary unless made durable. A newer timestamp does not settle authority. Unresolved conflicting facts leave the existing note unchanged and are reported.

Stored procedure approval does not authorize the current action. Consequential actions still need current-conversation permission under workspace safety rules. Stop at approval checks, failed steps or changed conditions and propose edits rather than silently revising the recipe.

## Recovery

Before replacing or deleting existing hand-written memory, preserve exact previous bytes. Generated indexes and hubs are rebuildable and need no snapshots; do not confuse them with handwritten rules, glossary or memory/index.md. Preserve snapshots under .memory-recovery/ at workspace root, outside active memory. Use the same protocol with or without Git, including uncommitted notes. New files need no snapshot. Git-ignore snapshots, exclude them from routine recall, and do not automatically prune. They can contain sensitive summaries; ignore rules are not encryption or access control. Secrets remain forbidden.

Optional recovery.py provides snapshot(root: Path, relative_path: str) -> Path and a backup-only CLI. Input is a POSIX workspace-relative memory/ path naming an existing regular file. Reject absolute/drive/backslash/parent traversal, source/parent symlinks and symlinked destination components before reading/writing. Create unique exclusive snapshots, compare copied bytes and confirm source stability before success. Failure never modifies the source. No restore/delete/replace engine or locking is added.

The agent re-reads before editing; changed source means stop and re-ground. This is a single-writer protocol, not a race-proof transaction system. Without Python use file tools to copy and verify; if preservation cannot be verified, stop. Restore only after showing snapshot/target and obtaining approval, preserving the current target first and checking indexes/hubs afterwards.

First setup excludes recovery from release copies. Upgrades retain the old workspace and recovery; separately copy recovery only if the owner wants it. Newly configured project memory receives the ignore rule too.

## Verification and rollout

Add failing unittest fixtures before implementation. Cover both leads, malformed procedures, dates/risk, fenced examples, path boundaries, copy failures and exact bytes. Keep workspace/project instructions aligned. Documentation tests check text, not obedience: run fresh-agent behavioral cases with disposable files and stub actions, no live connectors. Record model/client/OS and actual reads/actions; unavailable combinations are NOT RUN.

Review scripts against CODING_STANDARDS.md before committing; run direct pre-commit checks without enabling hooks. Stage only task-owned paths and document Local changes in CHANGELOG.md.

## Acceptance

1. Procedures lead tasks without becoming skills or supplying executable Also load steps.
2. Existing skill routing and ordinary memory remain compatible.
3. The incomplete-procedure probe fails checking and audit without writes.
4. External text cannot become standing authority under the documented policy.
5. Approved recipes never substitute for current-action permission.
6. Failed recovery or changed source stops edits; no-Git previous bytes remain recoverable.
7. Workspace and project scaffold agree; file-only operation needs no extra installation.

## Deferred work

Separate public-release plan: canonical maintainer source versus export, license, personal-default exclusions, optional skill packs and verified Codex/Claude Code/Cowork loaders. Separate retrieval plan: vocabulary/paraphrase evaluation at growing note counts before deciding on ranked local search. Promote a demonstration procedure only after a real run and owner approval; test fixtures are not genuine memory.
