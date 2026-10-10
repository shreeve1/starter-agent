# Adaptation list

The skeleton says what the loop does. It does not say how the loop keeps running on the owner's machine. That part is the owner's agent's job: find out how this harness and machine work, adapt the items below, and write down what was chosen.

The owner must verify the loop on a test system (or a test list of items that cannot reach real people) before a first real day. This spec does not design the loop runner; do not invent one beyond what the harness already offers.

## Find and adapt

1. **Re-prompt loop or scheduler.** How does this harness run the skill again later in the day? A built-in loop or repeat command, a scheduled task, a cron-style job, or the owner typing "startday" again? Pick the simplest one that exists. If none exists, the owner nudges it by hand.

2. **Watcher exit contract.** If the loop uses a small check script ("anything new?") between turns, decide exactly what it returns: which result means "wake the agent", which means "nothing yet, check later", and which means "day over, stop". Write this down in the skill so it does not drift.

3. **Notification mechanism.** How a message reaches the owner on this machine: desktop notification, chat, email to self, or only the approvals page. Test that one arrives. Keep private details out of it.

4. **Timezone.** The machine's clock and the owner's working timezone may differ. Find both and use the owner's for Hours.

5. **Where session transcripts live.** Only if the owner wants metrics (time spent, items done per day): find where this harness stores session logs, and read them read-only.

6. **Connectors and sign-ins.** Confirm the agent can read each Source with the owner's existing access. Note any sign-in that expires and how the loop reports it (a needs-you line, never a wait).

7. **File locations.** Confirm the research folder and approvals page are somewhere the owner actually reads, and that the owner's editor saves the checkbox tick in a way the agent can see.

8. **Stopping.** Confirm how the owner stops the loop at once if something looks wrong.

## Before a first real day

- Run one full day on the test system: gather, research, draft, tick one approval, execute it, reject one, wrap up.
- Check rule 5 directly: type a note and an answer in a research file, run a turn, and confirm both are untouched.
- Only then point it at real items.
