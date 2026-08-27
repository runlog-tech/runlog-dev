# model-routing-subagents

The real audit tool from RUNLOG's "I Tested Claude Code's Subagent Bug
(Why Do Others Fail?)" — checks which model each of your subagents
*actually served the request*, not just what its
`.claude/agents/<type>.md` frontmatter requested or what the harness
logged for itself.

There's an open Claude Code GitHub issue (#43869) with real repro
numbers claiming subagent `model:` frontmatter silently doesn't route —
a task pinned to Haiku quietly runs on Opus instead, and you'd never
know from the frontmatter alone. The same issue also showed that the
transcript's own logged `model` field can disagree with what actually
served the request — so this script doesn't stop at reading that field.
It decodes the served model out of each response's own tamper-evident
signature, the same verification method issue #43869's own most
rigorous commenters use, and cross-checks that against both the
frontmatter and the logged field.

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
and `.meta.json`, compares the `model:` frontmatter in your repo's
`.claude/agents/<agentType>.md` (DECLARED) against the model ID decoded
from each response's own signature (SERVED). A run is OK when both
agree and match what was requested; MISMATCH means the harness's own
logged field disagreed with what actually served it; IGNORED means the
served model never matched what was requested at all — the routing
failure issue #43869 describes; NO-SIGNATURE means no verifiable
signature was found (absence of proof, not a pass). Agent Teams
teammates (`taskKind: "in_process_teammate"`) are excluded by design —
they get their model from whoever spawned the team, a different
routing mechanism this checklist doesn't cover.

## What it found on this channel's own repo

11 real subagent runs audited, across 4 subagents (3 pinned to Haiku, 1
pinned to Opus). 11/11 signature-verified, zero mismatches — on this
machine, as of the video. That's not proof the GitHub issue is wrong;
it's specifically about Task-tool subagents, same as this checklist,
and other people are still reporting real routing failures on it. It's
proof this specific setup hadn't drifted yet, and this is what would
catch it the moment it did.

Most "silent" community reports of this bug likely trace to something
more specific than a raw routing failure: Claude Code's own docs
describe an `availableModels` allowlist that silently substitutes a
blocked model, with a warning that only shows in interactive sessions
— so a non-interactive/scripted run, or an enterprise allowlist
blocking a tier, can look identical to the bug from the outside. See
the video for the full explanation and the checklist behind *why* each
subagent got the tier it did.
