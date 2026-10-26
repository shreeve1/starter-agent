# Memory Templates

Markdown with small YAML frontmatter. A note is at most 6144 bytes and its `summary` at most 160 characters. Files state only what is true now.

## Promoted Topic File

For `preferences/`, `docs/` and `workflows/<topic>/`.

```markdown
---
title: Topic Title
summary: One line shown on the index, at most 160 characters
type: preference | doc | workflow | procedure | context
status: promoted
created: YYYY-MM-DD
updated: YYYY-MM-DD
topics: []
---

## Active memory

- Durable fact, rule or step.

## Related

- [Related topic](memory/docs/other-topic.md) - how it relates.

## Notes

- Changed YYYY-MM-DD: why, only when the reason still matters.
```

## Decision Memory File

Path: `memory/decisions/<topic>/decision-<slug>.md`.

```markdown
---
title: Short Decision Title
summary: One line shown on the index, at most 160 characters
type: decision
status: promoted
created: YYYY-MM-DD
updated: YYYY-MM-DD
topics: [<topic>]
---

## Decision

What was decided and why, in a few sentences.

## Notes

- Changed YYYY-MM-DD: why, only when the reason still matters.
```

## Procedure File

A shared procedure in `memory/workflows/<topic>/<slug>.md`, saved only with the owner's approval and made only of steps that were run and verified. Same frontmatter as a topic file with `type: procedure`; body sections: Trigger line, `### Steps` (numbered, exact commands), optional `### When something goes wrong`, `## Related`, `## Notes`.

## Client Memory Note

Path: `memory/<client_folder>/<subject>/<short>/<slug>.md`. One fact per note. All six keys required; `gate.py audit` checks them.

```markdown
---
type: client-memory
client: <short>
subject: <subject from schema.json>
title: One-line fact
verified: YYYY-MM-DD
source: "the owner said"   # or a file path, ticket or session
---
One fact in one to three sentences. Link related notes by path.
```

## Index

Workflows and decisions are listed in their generated sub-indexes (`indexes.py`); `index.md` carries one row for each sub-index, plus one row per other note.

```markdown
| Page | Type | Summary | Updated |
|------|------|---------|---------|
| [Title](memory/docs/slug.md) | doc | summary | YYYY-MM-DD |
```

## glossary.md

One row per entity, grouped under the sections that have content. Thin rows: short form, expansion, a few words of identity.

```markdown
## Systems
| Shorthand | Identity |
| --- | --- |
| mon1 | Monitoring server |
```

## rules.md

One row per trigger; pointers only. Skills as skill `name`, paths backticked and project-relative.

```markdown
| When | Lead | Also load | Note |
|---|---|---|---|
| Changing the alert rules | | `memory/workflows/monitoring/alert-rules.md` | |
```
