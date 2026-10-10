# Operator Profile (team)

The Operator Profile is the owner's identity and per-machine settings, in `.agents/operator-profile.json`. Team skills (for example `startday`) read it instead of hard-coded names and times. Friends edition: not used, skip this file.

It is a `local` file: a Release installs it at most once if it is missing, and never overwrites it. The owner's values are safe across updates.

Ask the owner for each value, one at a time. Never invent a value; leave the step until the owner answers.

## Keys

- `name`: the owner's name as it should appear in messages. Example: `"Alex Example"`.
- `email`: the owner's work email. Example: `"alex@example.com"`.
- `halo_agent_id`: the owner's numeric agent ID in the PSA (ticketing system). Whole number, no quotes.
- `timezone`: IANA timezone name. Example: `"America/Chicago"`. On Windows, `python -m pip install tzdata` first or it will not load.
- `own_short`: the short name of the owner's own company as used in the glossary. Example: `"acme"`.
- `word_shorts`: client short names that are also ordinary words, so they are only matched carefully. Example: `["comp"]`. (team) The shipped glossary has the shorts `comp` and `mal`, so start with `["comp", "mal"]`. Empty list if none.
- `automation_agents`: PSA agent IDs of automation accounts whose ticket actions are not a person's. Example: `[99]`. Empty list if none.
- `day_end`: hour the working day ends, 24-hour clock, whole number. Example: `17`.
- `scope_cutoff`: latest time the scope pass runs, `"HH:MM"`. Example: `"15:00"`.
- `mcp_server`: the name of the MCP server entry (in the owner's MCP config) that exposes the PSA tools. Example: `"my-psa-server"`.
- `transcriber_socket`: path to a meeting transcriber socket. Leave `""` unless the owner runs one; on Windows and macOS it stays empty.
- `desktop_notify`: `true` to show desktop notifications (Linux desktops with `notify-send`). Default `false` on Windows and macOS.

## Finding the PSA agent ID

Work it out with the owner: ask them to open their own agent/user record in the PSA admin screens and read the numeric ID, or, if the PSA tools are connected, look up the owner by email and show them the result to confirm. Ask the owner to confirm the number before saving it.

## Template

Replace every `<...>` with the owner's answer (numbers and `true`/`false` without quotes):

```json
{
  "name": "<owner name>",
  "email": "<owner email>",
  "halo_agent_id": <number>,
  "timezone": "<Area/City>",
  "own_short": "<own company short name>",
  "word_shorts": [],
  "automation_agents": [],
  "day_end": <hour>,
  "scope_cutoff": "<HH:MM>",
  "mcp_server": "<server name>",
  "transcriber_socket": "",
  "desktop_notify": false
}
```

## Check it loads

Run the team startday tests (`CHECKLIST.md`). A missing key, bad JSON or unknown timezone stops with a message naming the problem.
