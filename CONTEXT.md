# Starter Agent — Shared Language

Shared terms for personal memory, research, and reusable guidance in this workspace.

## Language

**Edition**:
One of the two standalone builds of this workspace made for a different audience: the friends edition or the team edition (which also carries a memory seed). Each is its own folder with its own history and its own independently chosen skill list; neither is built from the other.
_Avoid_: version, fork, flavor

**Release**:
A numbered folder of one Edition's files that the person running that Edition has their own agent apply. It is built one-way from the source workspace and is never pulled from a remote.
_Avoid_: update, sync, pull

**Manifest**:
The file shipped in every Release that classifies each file by how an update may treat it: merged on every release, seeded once, or left to its owner.
_Avoid_: file list, lockfile

**Pristine Snapshot**:
The unedited copy of an applied Release, kept in the owner's own history and used as the common base when merging the next Release.
_Avoid_: applied tag, backup, baseline

**Schema**:
The one list of valid Client Subjects, memory topics and per-client document folders for a workspace. Each Edition ships its own, and the owner may change it.
_Avoid_: taxonomy, config

**Client Short Name**:
The one canonical lowercase identifier for a client, listed in the glossary with the client's identity. It names the client's folder; the client is resolved by that identifier, never by matching names.
_Avoid_: client code, alias

**Client Memory**:
The lasting facts about a client (environment, contacts, quirks, standing decisions, temperature), kept in personal memory as small single-topic notes grouped by Client Subject. It holds what is true about the client, not what happened on a task.
_Avoid_: client notes, client doc, one big client profile

**Client Subject**:
A named area of client knowledge that groups Client Memory notes across all clients, such as `contacts` or `temperature`. Each subject holds one folder per client, which may contain many small notes.
_Avoid_: category, topic (topic is used for non-client memory files)

**Temperature**:
The Client Subject recording what pleases or frustrates a client, as dated observations with their source, never guesses about personality.
_Avoid_: sentiment, mood, satisfaction score

**Procedure**:
A saved way of doing one workflow, made only of steps that were run and verified. A **Client Procedure** is kept per client and may name the client; a **Shared Procedure** applies to every client and names none.
_Avoid_: runbook, SOP, playbook

**Path to Close**:
The part of every research record that states what still stands between the item and closure, who owns each step, and the next drafted action. Research exists to advance it.
_Avoid_: next steps, resolution plan

## Relationships

- An **Edition** is built one-way from its source workspace: changes an owner makes never flow back, and each **Release** is applied by the owner's own agent after talking the plan through with the owner.
- An **Edition**'s skill list is chosen on its own, so a skill left out of one **Edition** is never restored because the other includes it.
- A **Release** is merged against the **Pristine Snapshot** of the previous Release, never against the owner's edited files, so the owner's changes survive each update; a first install has no previous snapshot.
- A **Release** never removes a **Schema** entry that the owner's notes still use: the change is held until those notes are migrated or validated, and the audit keeps failing any note whose subject is not in the **Schema**.
- **Client Subject** and topic values come from the **Schema**; an agent adds one only with the owner's approval.
- **Client Memory** is the single home for lasting client facts; other memory topics hold tool quirks, not client facts.
- A **Client Memory** note belongs to exactly one client and one **Client Subject**; a fact spanning subjects is filed under the subject a future task would look in first and linked from the other.
- A **Shared Procedure** applies to a client even when the client has no **Procedure** for that workflow; a **Client Procedure** wins where it differs.
- A **Procedure** is corrected in place; git is the history.
- A **Path to Close** is rewritten each time research advances: remaining steps, who owns each one, and the next drafted action.