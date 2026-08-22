# rebuild-your-claude-md

The two guardrail commands from RUNLOG's "Rebuild Your CLAUDE.md, Don't
Accrete It" — the actual files this channel runs on its own repos, not a
simplified rewrite for the video.

`CLAUDE.md` only auto-loads itself, not a `memory/` folder. Every time you
update it directly, you're one step closer to it reading like a changelog
instead of an index of what's true right now. These two commands are the
guardrail: one stops new content from defaulting into `CLAUDE.md`, the other
checks whether old narrative is creeping back in.

## Install

Copy `.claude/commands/` into your own repo's root (or merge it into an
existing `.claude/commands/` directory):

```
cp -r .claude/commands/* /path/to/your-repo/.claude/commands/
```

## `/triage-memory`

Classifies whatever you'd normally jam into `CLAUDE.md` — a fact, a
decision, a bug fix — into one of four buckets (standing fact / open
decision / decision record / changelog), and routes each to the right file
instead. Shows the routing table and asks before writing anything.

Assumes a `memory/current_state.md` / `memory/pending_decisions.md` /
`memory/video_ideas.md` / `memory/session_history.md` layout — adjust the
paths in Step 2 to whatever your own repo actually uses.

## `/audit-claude-md`

Scans `CLAUDE.md` for narrative/changelog language creeping back in (dates,
"decided on," "fixed a bug where"), confirms every file it points to still
exists, and measures its token count against a baseline. Diagnostic only —
it reports, it doesn't edit.

## Why this matters

Official tooling (Anthropic's own `claude-md-management` plugin, and the
newer `/checkup` command) restructures `CLAUDE.md` — dedupes it, splits it,
adds to it. None of it asks whether a given line belongs there at all.
That's the actual gap these two commands close. See the video for the full
before/after: 6,080 tokens down to 912 on this channel's own file, run for
real across three separate repos.
