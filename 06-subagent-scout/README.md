# subagent-scout

The real Claude Code skill from RUNLOG's video on finding subagent
candidates in your own session history — not from a typed description,
from the tool calls you've actually repeated.

Scans a project's real Claude Code session transcripts
(`~/.claude/projects/<encoded-path>/*.jsonl`) for tool-call sequences
that repeat at least 3 times, judges each one against a 4-question
checklist (retrieval vs. judgment, stateless vs. context, cheap to
verify, blast radius), interviews you one question at a time before
doing anything, and — only on confirmation — drafts the
`.claude/agents/*.md` file for you. Declines are logged too, so a
declined pattern stays declined on future runs.

## Install

```
cp -r SKILL.md scripts ~/.claude/skills/subagent-scout/
```

## Usage

Ask Claude Code directly, e.g. "find candidates for subagents in this
repo", or run the detector by hand:

```
python3 ~/.claude/skills/subagent-scout/scripts/detect_patterns.py --repo-path <target project dir>
```

`detect_patterns.py` is real, inspectable code, not an LLM guess — it
reports two signals per candidate: `cross_session_count` (a durable
habit) and `max_single_session_count` (a single session's context got
bloated by this loop, even if it never recurred). It automatically
skips any signature already recorded in `.claude/subagent-scout-log.md`
in the target repo, so a decline stays declined.

## What it found on this channel's own repo

Dogfooded against RUNLOG's real session history (and, separately, an
unrelated channel's repo, with no hints carried over): both times it
independently found the same real pattern — opening rendered thumbnail
frames one at a time to check them, 61x in one sitting on this repo,
104x on the other. Built `render-frame-fetcher` (Haiku, retrieval only
— final design judgment stays with the main session) both times, same
verdict, zero tuning between runs.

It also correctly declined two real candidates: a `grep`-then-`Read`
pattern that passes every checklist box but is already cheap where it
is (delegation overhead would exceed the saving), and a repeated
browser-automation loop that fails outright because each step depends
on the last screenshot — not a one-shot task a subagent can hold.

Re-run live during this video's own production, it caught its own
real limitation: a shorter variant of an already-solved signature slid
past the sticky-skip's exact-string dedup and got re-flagged as new.
See the video for the full walkthrough, the real cost numbers, and
where the checklist says no.
