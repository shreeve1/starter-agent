---
name: talk-it-through
description: |
  Stress-test a plan or process against the team's shared language and previously recorded decisions, sharpen fuzzy terminology, maintain a CONTEXT.md glossary inline, and automatically record what was settled.

  Use when the user wants to pressure-test a plan, workflow, or document, sense-check a decision, or mentions "talk it through".
---


# Talk It Through

## Workflow

Interview me to reach a shared understanding of this plan, process, or document — but apply the 80/20 rule. Spend your questions on the vital few decisions that determine most of the outcome: the ones that are hard to reverse, that other decisions hang off of, or where getting it wrong is expensive or embarrassing. Skip the trivial many.

Before each question, ask yourself: "Does this decision meaningfully change the plan, or am I just walking a branch for completeness?" If the branch is low-stakes, easily reversible, or has an obvious default, state your recommended default in one line and move on — do not turn it into a question. Prune branches that don't change what we do.

Resolve dependencies in order — settle a foundational decision before the ones that depend on it — but only descend into a sub-branch when the answer would actually shift the plan. For each real question, provide your recommended answer.

Ask the questions one at a time, waiting for feedback on each question before continuing.

Always output questions as plain text in the chat. Never use the `question` tool — this is a back-and-forth conversation, not a multiple-choice form.

Stop when the remaining open questions are all low-stakes detail. At that point, say so and summarize the defaults you're assuming for the rest rather than continuing to probe.

If a question can be answered by checking existing material (the memory folder, prior decisions, a referenced document, or the workspace), check it instead of asking. If it can be answered by a web search (a vendor's published policy, a product's documented behavior, current guidance), search the web instead.

## Supporting Information

### Awareness of existing language and decisions

At the start of a session, look for what's already been decided so you can challenge against it:

- A `CONTEXT.md` at the workspace root — canonical vocabulary: contested/overloaded terms with a chosen form and aliases to avoid ("which meaning?"). See [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).
- `memory/glossary.md` — the entity directory: shorthand -> full identity ("who/what is this?"). CONTEXT.md and glossary.md are siblings — keep contested vocabulary in CONTEXT.md and plain label expansions in glossary.md.
- `memory/index.md` — read the whole Promoted Memory table. This is the discoverability map for everything in memory, not just decisions: preferences, workflows, docs, and decisions all appear here (workflows and decisions through the generated sub-indexes `memory/workflows/index.md` and `memory/decisions/index.md`, linked from the table).

Read the index up front, but pull full memory files lazily: open a specific entry (for example a row under `memory/preferences/`, `memory/docs/`, or a file listed in the workflow/decision sub-indexes) only when its summary looks like it might inform or contradict the topic being discussed. Don't eagerly read the whole memory tree every session. See [DECISIONS-FORMAT.md](./DECISIONS-FORMAT.md) for decision specifics.

Create files lazily — only when you have something to write. If no `CONTEXT.md` exists, create one when the first term is resolved. Use only the known sections from [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md); do not invent unresolved terms, relationships, or example dialogue just to fill the file.

### During the session

#### Challenge against the glossary

When the user uses a term that conflicts with the agreed language in `CONTEXT.md`, call it out immediately. "Your glossary defines 'client' as a billing entity, but you seem to mean the day-to-day contact — which is it?"

#### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'sign-off' — do you mean the manager's approval or the client's acceptance? Those are different gates."

#### Discuss concrete scenarios

When relationships between people, steps, or documents are being discussed, stress-test them with specific scenarios. Invent realistic situations that probe edge cases and force the user to be precise about who does what, in what order, and what happens when something is missing.

#### Cross-reference with what's recorded

When the user states how something works, check whether the recorded memory or the referenced document agrees. If you find a contradiction, surface it: "Last month you decided invoices go out on the 1st, but you just said month-end — which is right?"

#### Maintain CONTEXT.md inline

When a term is resolved, update `CONTEXT.md` right there. Don't batch these up — capture them as they happen. Use the format in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).

`CONTEXT.md` is a glossary of agreed terms and relationships — nothing else. Keep it free of step-by-step procedure, task lists, or decision rationale. Those belong in the document being discussed or in a memory decision. Plain shorthand -> identity expansions belong in `memory/glossary.md`, not here.

Leave sections absent until they have real content. For example, do not add `Example dialogue` until there is a useful real or synthesized exchange that clarifies the terms.

### Wrapping up — record what was settled automatically

This step is automated. Do **not** ask "do you want to record this?" A session wraps up when the user says to stop/wrap up, when you determine the remaining questions are low-stakes detail, or before you give the final summary.

A talk-it-through session is itself the approval: the user was actively in the loop settling things. So anything **clearly settled in-session** is promoted directly to its proper topic file. Anything you **inferred but the user did not explicitly confirm** is also written automatically per the AGENTS.md capture rule, but mark it `unverified` in Notes. Do not ask first. There are no candidates.

#### 1. Identify what was settled, and route it by type

For each settled item, pick the type by what it is. When ambiguous, default to **decision**.

- **decision** — a choice about what gets done, who does it, or a process or boundary. → write to `memory/decisions/<topic>/decision-<slug>.md` per [DECISIONS-FORMAT.md](./DECISIONS-FORMAT.md).
- **preference** — how the user wants the assistant to behave or communicate. → merge into `memory/preferences/` (e.g. `assistant-style.md`).
- **voice** — a preference specific to voice-mode interaction. → merge into `memory/voice/voice-mode.md`.
- **workflow** — a repeated habit or sequence of steps. → merge into `memory/workflows/<topic>/`. Verified steps for one workflow are a Procedure, not a workflow note: a shared Procedure is written only through an owner-approved change, never auto-captured.
- **doc** — an important reference, link, or path to remember. → merge into `memory/docs/important-docs.md`.
- **guide** — a reusable, redacted ticket-resolution note. Do NOT auto-write; Ticket Guides are saved only through an owner-approved change (one `ticket-guide` approval). Leave it for that flow.
- **glossary entity** — a shorthand -> identity mapping (client short name, nickname, acronym, codename). → merge into `memory/glossary.md`. Contested/overloaded terms instead go to `CONTEXT.md` inline, per above.

Pick the topic for a workflow or decision from the `topics` list in `memory/schema.json` (a new topic only with the owner's OK). After writing one, run `python3 .agents/skills/personal-memory/indexes.py` (regenerates the topic sub-indexes) and `gate.py audit`. 15-file rule: a memory folder holding more than 15 `.md` files directly gets topic subfolders plus a generated index; `gate.py crowded` reports it.

For decisions, follow [DECISIONS-FORMAT.md](./DECISIONS-FORMAT.md). For preferences, voice, workflows, and docs, follow [PROMOTED-MEMORY-FORMAT.md](./PROMOTED-MEMORY-FORMAT.md) — these merge into the owning topic file rather than creating one file per item. Both use the matching template in `memory/TEMPLATES.md` and write with `status: promoted`.

#### 2. Before writing, check for existing entries

Scan `memory/index.md` and the relevant topic folder for a matching or superseded entry. If one exists, update it (bump `updated`, note what changed) rather than creating a duplicate.

#### 3. Update the index and log

Update `memory/index.md` (Promoted Memory table; workflows/decisions only need their sub-index, linked from `memory/index.md`) and append a `memory/log.md` entry, matching the formats in `memory/TEMPLATES.md`. If updating an existing entry, update its existing index row date/summary instead of adding a duplicate. Run `python3 .agents/skills/personal-memory/indexes.py` and `gate.py audit` after writing.

#### 4. Tell the user

In one short line, say which items you recorded, their type, and where.

Skip an item only when it's purely transient (a one-off detail with no future relevance) or when it merely restates an existing recorded entry without changing it. If nothing qualifies, say so in one line.

Never store passwords, secrets, or other credentials in memory — omit them automatically and never ask. Client and third-party details (names, environments, contacts, config facts) are allowed in memory, except in Ticket Guides, which stay redacted per `memory/README.md`.
