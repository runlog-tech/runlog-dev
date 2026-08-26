# model-routing-subagents

The real audit tool from RUNLOG's "I Tested the Claude Code Subagent
Bug. It Didn't Happen." — checks which model each of your subagents
*actually* ran on, versus what its `.claude/agents/<type>.md` frontmatter
requested.

There's an open Claude Code GitHub issue (#43869) with real repro
numbers claiming subagent `model:` frontmatter silently doesn't route —
a task pinned to Haiku quietly runs on Opus instead, and you'd never
know from the frontmatter alone. This script reads the actual session
transcript, not the request, so it catches that kind of drift instead
of trusting the config.

## Install

Copy the script into your own repo's root (same directory as your
`.claude/agents/`):

```
cp audit_subagent_models.py /path/to/your-repo/
cd /path/to/your-repo
```

## Usage

```
python3 audit_subagent_models.py [session_id]
    No args: audits the most recently modified session with subagent data.

python3 audit_subagent_models.py --all
    Aggregates every subagent run across every session in this project,
    tallied per subagent type.
```

Reads `~/.claude/projects/<your-repo-slug>/<session-id>/subagents/agent-*.jsonl`
and `.meta.json`, compares the real `model` field from each transcript's
assistant turns against the `model:` frontmatter in your repo's
`.claude/agents/<agentType>.md`. Agent Teams teammates
(`taskKind: "in_process_teammate"`) are excluded by design — they get
their model from whoever spawned the team, a different routing
mechanism this checklist doesn't cover.

## What it found on this channel's own repo

12 real subagent runs audited, across 4 subagents (3 pinned to Haiku,
1 pinned to Opus). 12/12 routed correctly — zero drift, on this
machine, as of the video. That's not proof the GitHub issue is wrong.
It's proof this specific setup hadn't drifted yet, and this is what
would catch it the moment it did.

See the video for the full checklist behind *why* each subagent got
the tier it did.
