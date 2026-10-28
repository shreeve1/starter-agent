---
name: drawio
description: Shared draw.io canvas that James edits in a browser while you edit the same .drawio file on disk. Use when James asks to talk about or brainstorm a subject with this skill (draw a seed diagram first); when planning or brainstorming a flow, workflow, process, agent or bot design, or system structure with James; when he asks for a diagram or flowchart he can edit himself; when starting, stopping or checking the draw.io server; or when reading or editing any .drawio file.
---

# drawio

James drags shapes in the full draw.io editor in his browser; you read and edit the same `.drawio` file on disk. You take turns. A tiny Node server (no dependencies) serves the editor page and the files; the editor itself loads from `embed.diagrams.net`, so his browser needs internet, but diagrams never leave the host.

`<skill-dir>` below is this skill's base directory, as your harness reports it when the skill loads. Paths differ per machine, so use that one.

## Where diagrams go

Place each diagram beside the artifact it illustrates. Use the first matching route:

- **Superpowers planning:** when writing or executing a plan, save the diagram beside the plan with the same basename. Superpowers' default is `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`, so the companion is `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.drawio`.
- **Superpowers brainstorming/design:** when brainstorming or shaping a design, save the diagram beside the design/spec it is producing, using the same basename. Superpowers' default is `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`, so reserve the companion there even before the spec is written.
- **Personal memory:** when no Superpowers planning or brainstorming route applies and the project has `memory/`, use the `personal-memory` skill to identify or create the related memory note, save the companion `.drawio` beside that note, and add a relative link from the note to the diagram. Examples: `memory/docs/topic.md` → `memory/docs/topic.drawio`; `memory/decisions/projects/decision-feature.md` → `memory/decisions/projects/decision-feature.drawio`.
- **Fallback:** when neither Superpowers nor project memory applies, save to `cwd/drawio/<subject>/diagram.drawio`. The file extension is `.drawio`, not `.io`.

Start the server with `--dir` set to the root containing the selected location: normally the project root, or `cwd` for the fallback route.

## Find before create

Reuse the relevant diagram instead of creating a second one:

1. Resolve the owning artifact and storage route above, then search that location and the project root for existing `.drawio` files matching the subject, plan/spec basename, memory-note basename, or an obviously related name. Inspect the running server's diagram list too when available.
2. If a relevant diagram exists, report its path (or paths) and ask James to confirm which one to open. Do not create or edit a diagram until he confirms.
3. After confirmation, serve and open that diagram, then iterate on it. If several candidates exist, list each path and ask him to choose one.
4. If no relevant diagram exists, create one at the selected storage location and give him its link.

## Question and decision notes

Use notes throughout the diagram's life, not only during brainstorming:

- Reserve a clear column on the right for unresolved questions, decisions needing confirmation, assumptions, risks, and other items James can answer or correct.
- Keep the main flow or structure separate from this question column. Stack active notes vertically and keep their wording short and specific; use the yellow note style from `reference/format.md`.
- When a question is answered, keep its note as history. Mark it answered, move it below the active notes, or consolidate related answered notes into an `Answered decisions` note. Do not remove an answered note just because it is resolved.
- As new questions appear, add them to the active right-hand column and stack or consolidate the answered history to preserve room. Update the notes in the same turn when a decision is settled.

## Start, stop, status

```sh
node <skill-dir>/scripts/drawio.mjs start --dir <project root> --host <NetBird IPv4> --url-host <NetBird IPv4>
node <skill-dir>/scripts/drawio.mjs status
node <skill-dir>/scripts/drawio.mjs stop
```

- Always find the machine's NetBird IPv4 with `netbird status` or from the dotfiles `AGENTS.md` table, and pass it to both `--host` and `--url-host`. The printed link must use the NetBird IPv4, never `localhost`.
- On a native host, bind directly to its NetBird IPv4. aidev is `100.95.230.15`; work is `100.95.235.60`; itan8n is `100.95.224.218`; surftop is `100.95.222.42`.
- WSL on work is the exception: NetBird runs on Windows, so bind the WSL server to `0.0.0.0` but pass work's NetBird IPv4 (`100.95.235.60`) to `--url-host`. Use `node <skill-dir>/scripts/drawio.mjs start --dir <project root> --host 0.0.0.0 --url-host 100.95.235.60`.
- Run `status` before `start`. `start` replaces the running server, and another session may be using it: if it serves a different folder, ask James before replacing it (any tab open on the old folder switches saving off). Other flags: `--port`, `--idle-minutes` (default 240; it exits by itself after that long without a browser request).
- Give James the printed `url`. Link straight to a diagram with `<url>edit?file=<path relative to --dir>`; a path that doesn't exist yet opens a blank diagram that is created on first Save.
- Run `stop` when the session's diagram work is done.

## Taking turns

The file on disk is the shared state. The page saves only when James presses Save (Ctrl+S), and it polls the file every 2 s.

1. **When James reports that he updated, changed, or edited the diagram, treat that report as confirmation that he saved it.** Read the file immediately and proceed; do not ask him to confirm saving again. If he has not reported a change and you need to edit an existing diagram, ask him to save first. (A new diagram has nothing to save: write it, then give him the link.) If he changed it since your last turn, say in a line or two what he changed (added, moved, relabelled, deleted), because that is his half of the conversation.
2. **Edit** following `reference/format.md`.
3. **Tell him** what you changed. His page reloads by itself when he has no unsaved edits.
4. If he had unsaved edits when you wrote, his page shows a banner instead: Reload takes your version, Save as copy keeps his as `<name>-mine.drawio`. His tab then edits the `-mine` copy. Read both, merge into the original, give him the original's link, and delete the copy once he has switched back and agrees.

Before writing or editing any `.drawio` XML, read [`reference/format.md`](reference/format.md).

## Kick-off: "let's talk about X and brainstorm"

When James invokes this skill along with a subject to talk about, invoking the skill means yes to the canvas. First find any relevant existing diagram. Your first message either asks James to confirm a matching diagram to open or gives him a new seed diagram to react to:

1. **Load the `talk-it-through` skill** and follow it for the conversation. This section replaces its visual companion offer with the draw.io canvas; everything else in that skill still applies.
2. **Look before you draw.** Read what the subject points at: the plan, spec, code, notes or earlier conversation it names or that obviously relates to it. Stop once you can sketch how it works today, or what he seems to want. When there is little or nothing to read, seed from the subject alone: a topic map of the usual parts of such a thing, mostly `?` labels, is still a better start than a blank page.
3. **Pick the shape** that fits the subject:
   - **Flow** (steps, a process, a pipeline, a bot or agent loop, a request path): a rough flowchart of what you know.
   - **Structure** (a system, its parts and how they connect): boxes for the parts, arrows for the connections.
   - **Topic map** (anything still fuzzy: an idea, a decision, a problem): the subject in the centre, branches for the parts, goals, constraints and options you found or he named.
4. **Seed it:** 5 to 12 main shapes. Use his words for labels. Anything you filled in yourself ends its label with a question mark after a space ("Agent triages ?"). Add 2 to 4 yellow notes (200×80) in the right-hand question column for the open questions whose answers would change the diagram most. Keep the question column separate from the main flow or structure. Put it where the placement rules above say, named after the subject.
5. **Serve it:** `status`, then `start` if needed, and check the XML.
6. **First message:** the direct link; one or two lines on what you drew and what you based it on; then the `talk-it-through` first-message pattern (a one-line subject counts as "they haven't said what they want", even when the files you read fill in a lot), ending with its single question. Make that question one the canvas can answer too: "fix it in the text or on the diagram, whichever is quicker."

From then on, follow **Taking turns** and the rules below.

## In brainstorming

This canvas is the editable form of the `talk-it-through` skill's visual companion. When a flow, sequence of steps, set of states, or structure comes up, offer to sketch it on the canvas instead of describing it, in a message of its own. When he has already asked for a diagram, or opened with the kick-off above, skip the offer and follow **Find before create**: reuse a confirmed relevant diagram, or create one only when no relevant diagram exists. Then:

- Sketch the current understanding in the confirmed existing diagram or the newly created one: rough, labelled, few shapes. Put each open question or guess in a yellow note shape beside the step it concerns, so he can see what to correct.
- Keep the diagram in step with the conversation: when he settles something in text, update the canvas in the same turn and say so.
- Read his edits as answers. A deleted box is a rejected step; a new arrow is a dependency he cares about. Confirm what you read before building on it.
- Decisions belong in the spec or design doc; the diagram illustrates them. When you next write that doc, link the diagram's path from it.
