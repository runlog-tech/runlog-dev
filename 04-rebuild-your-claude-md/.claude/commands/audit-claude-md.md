---
description: Check CLAUDE.md for narrative/changelog creep back into the lean index
allowed-tools: Read, Grep, Bash
---

`CLAUDE.md` in this repo is meant to stay an index and a set of standing operating rules — not a log (see its own "Keeping this file honest" section). This command checks whether it's drifted back toward accretion since the last rebuild.

## Step 1: Scan for log-shaped content

```bash
grep -n -E "2026-[0-9]{2}-[0-9]{2}|decided on|user feedback|fixed a|caught a|turned out|found that" CLAUDE.md
```

Any hit is a candidate for "this reads like what happened, not what's true" — the exact failure mode this file was rebuilt to avoid.

## Step 2: Check every fact still resolves

For each pointer or fact `CLAUDE.md` names (a file path, a memory file, an external doc), confirm it still exists and still says what `CLAUDE.md` implies it says:

```bash
for f in memory/current_state.md memory/pending_decisions.md memory/video_ideas.md memory/session_history.md memory/experiments.md; do
  [ -f "$f" ] && echo "ok: $f" || echo "MISSING: $f"
done
```

## Step 3: Measure

```bash
python3 -c "print(f'{len(open(\"CLAUDE.md\").read())//4} tokens (est.)')"
```

Compare against the token count recorded at the last rebuild (see `memory/video_ideas.md` entry 6's demo trail for the baseline). A meaningful climb back up is the signal it's time to run `/triage-memory` retroactively on recent history, or do a full delete-and-rebuild from `memory/current_state.md` again.

## Step 4: Report

List every Step 1 hit with a one-line verdict (belongs in `memory/session_history.md` / `pending_decisions.md` / `video_ideas.md` instead, or is a rare legitimate exception), any Step 2 misses, and the Step 3 number. Don't edit anything automatically — this is a diagnostic, not a fix. Point to `/triage-memory` or a manual rebuild as the next step.
