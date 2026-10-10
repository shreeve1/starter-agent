# Skeleton SKILL.md

Copy everything below the line into `.agents/skills/startday/SKILL.md`. Replace every `<fill in: ...>` with the owner's interview answer. Keep the six rules word for word.

---

```markdown
---
name: startday
description: Start-of-day loop over <fill in: what a work item is> from <fill in: where items come from>. Gathers the day's items, researches each one read-only into its own research file, drafts every change as an approval to tick, and executes only ticked approvals, until <fill in: when the day ends>. Use for "startday", "start my day", or when the loop re-prompts.
---

# startday

## Rules

1. Research is READ-ONLY. The loop gathers and prepares. It never changes anything in the owner's systems.
2. Every change is an APPROVAL the human ticks: a checkbox in a document the human reads. A change is executed only after the tick.
3. The loop NEVER blocks waiting on the human. It parks the item, moves on, and re-checks later.
4. Each work item gets its own research file with a section named "Path to Close" that says what is still needed to finish the item.
5. The human's edits always survive. The loop never overwrites text the human typed.
6. Empty or blank answers count as not answered.

Owner settings:
- Work item: <fill in: what a work item is and what separates two items>
- Source: <fill in: tool or connector and how to read it>
- Mine today: <fill in: which items count, which to skip>
- Hours: <fill in: start time, stop-new-research time, end time, timezone>
- May read: <fill in: allowed sources>; never read: <fill in: off limits>
- Changes needing approval: <fill in: list>, plus anything else that writes or sends.
- Research files: <fill in: folder>, one file per item. Approvals page: <fill in: path>.
- Notify by: <fill in: method>. No private details in notifications.
- Never: <fill in: hard limits>

## Start

1. Check the clock against Hours. Outside them, say so and stop.
2. Open the approvals page and research folder; create them if missing (never overwrite).
3. Handle any approvals ticked since the last run (see Check approvals).

## Gather

1. Read today's items from Source, keeping only "Mine today".
2. Order them: due soonest first, then the rest.
3. Note new, changed and gone items. A gone item: cancel its open approvals and mark its research file closed.

## Research

For each item, until the stop-new-research time:
1. Open or create its research file. Read the owner's notes and answers first; they are the newest facts.
2. Read the item and related sources (read-only).
3. Write dated findings and rewrite Path to Close: remaining steps, who owns each, next approval id.
4. Something only the owner knows: add a question with an empty `Answer:` line. Park the item and move on.
5. Stop at a wall: a change, a person, or a sign-in.

## Draft approvals

For each change research wants, add one checkbox line to the approvals page with title, exact target and exact text. Never draft while the item has unanswered questions the change depends on.

## Check approvals

Every <fill in: check interval>, and at Start:
- `[x]` ticked: execute it (next step).
- `[-]` rejected: record the reason in the research file; do not redraft.
- Body edited by the owner: ask once "Send your edited version?".
- Item changed since the draft: cancel and redraft.
- Unticked: leave it; move on.

## Execute ticked

Do exactly what the ticked line says, nothing more. Check it took effect. Mark the line done with the time, or failed with the reason. Update the research file.

## Wrap-up

At <fill in: what done for the day means>: stop starting research, write a short summary (items by status, approvals waiting, open questions, needs-you lines), notify by the owner's method, and stop the loop.
```
