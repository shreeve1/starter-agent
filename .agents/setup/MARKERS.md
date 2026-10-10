# Edition markers

The maintainer keeps one source for both editions. Text meant for only one edition is wrapped in marker lines:

```

```

When a Release is built, the export keeps the text inside `edition:team` for the team edition and drops it for friends, drops `edition:owner` text from both, and removes the marker lines themselves. An unbalanced or unclosed marker fails the build.

So owners normally never see these markers.

## If you find one

A leftover `<!-- edition:... -->` line in a shipped file is a bug in that Release. Do not try to interpret it, and do not delete the text around it on a guess. Tell the owner, and ask them to report the file name and line to whoever maintains their edition. The owner may remove the stray line itself; the next Release merges normally.
