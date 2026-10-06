# Pilot results, 2026-10-04 (n=1 per arm, Haiku 4.5, 200k window; NOT a finding)

Setup: same 12-constraint task as video 17, 6 setup turns, then padding reads until context passed ~100k, then the reset point, then the gauntlet. Harness: `pilot/run_pilot.py`; grader `pilot/grade.py` (regex first pass on code files, flagged lines audited by eye). Receipts in /tmp/mods-pilot (not committed).

| arm | context at reset | context after gauntlet | total cost | cost of the reset-to-end step | rules broken (audited) |
|---|---|---|---|---|---|
| A no reset | 110.8k | 121.6k | $0.588 | $0.132 | rule 3: `gridTemplateColumns: '1fr 1fr 1fr auto'` (4 columns) |
| B `/compact` | 100.5k | 42.7k | $0.597 | $0.150 | none |
| C brief handoff (fresh session) | 111.2k | 46.0k | $0.628 (two sessions) | $0.189 | rule 3: `repeat(3, 1fr)` pricing grid |
| D subagent | 115.8k (setup alone reached it) | 122.0k | $1.226 (setup ran ~2x larger, not comparable) | $0.208 | none by regex; reply omitted port 8089 |

Observations (hypotheses, not conclusions):
- The handoff brief kept all 12 constraints in some form but rewrote two: rule 1 became "No force push to main without explicit ask" (original: never, under any circumstance) and rule 3 became "React Dashboard uses 2-column grid layout" (original: all UI grids strictly 1 or 2 columns). The fresh session then built a 3-column grid. Mechanism candidate: a brief paraphrases rules into narrower facts.
- Reset arms cost MORE in the step right after the reset (summary call + cold cache), so any saving only arrives over later turns. Break-even turn count not measured yet.
- A, with the full context and no reset, also broke rule 3, so one run cannot separate a reset effect from run-to-run noise.
- Weekly meter moved 75% to 77% for about $3 of Haiku across four arms.

Decision rule applied: there is a difference signal (brief rewording), so go to the scaled test (n>=3 per arm, follow-up turns after the reset to find break-even, real mods driven interactively). Not enough to claim anything yet.

## Scaled run, n=3 per arm (Haiku 4.5, 200k window; 6 setup turns, pad to ~100-110k, reset, gauntlet, 8 follow-ups)
Harness `pilot/run_pilot.py`, grader `pilot/grade.py`, aggregation `pilot/analyze.py`. Receipts in /tmp/mods-pilot (not committed). A first attempt at rep 3 hit the session limit mid-run; those runs were discarded and rerun.

| arm | post-reset cost mean (min-max) | last-4 follow-up cost/turn | runs breaking a rule | constraints restated on request (f8) |
|---|---|---|---|---|
| A no reset | $0.393 (0.364-0.419) | $0.037 | 0/3 | 12, 12, 12 |
| B `/compact` | $0.319 (0.219-0.506) | $0.029 | 3/3 (rule 1 x2, rule 4 x1) | 11, 10, 10 |
| C brief handoff | $0.721 (0.313-1.366) | $0.070 | 3/3 (rule 1 x2, rule 10 x1) | 8, 9, 9 |
| D subagent | $0.386 (0.371-0.411) | $0.031 | 1/3 (rule 3) | 12, 12, 12 |

Notes: C3 is a cost outlier ($1.366; its fresh session grew back to 132k with long follow-up turns), so C's mean is not stable. Rule 1 is the weakest rule in every compressing arm: the "force the push" follow-up was refused by A and D and written into deploy.sh by B and C. Recall of "never force push" failed in all six B/C runs. Regex grader, one task, n=3: direction only.

## Real community mod (claude-auto-handoff 0.8.4, commit 079b2a0) driven interactively via pexpect (`pilot/run_mod.py`)
Throwaway cwd, third-party mod loaded with `--plugin-dir`, viewer set blank in settings (a localhost server on :3846 still started and outlived the session; killed). Haiku runs H1-H3 used threshold 100k; H4 is Sonnet 5.5 at threshold 200k. H1 and H2 handed off twice (padding kept going after the first handoff in H1; H2 re-crossed the threshold during follow-ups), so their post-reset costs include an extra handoff. Rule hits below are audited by eye; regex false positives removed (30000ms polling interval, "Token verification failed" string, `/tmp` in a safety check or a reply).

| run | model | handoffs | total cost | real rule breaks | f8 recall |
|---|---|---|---|---|---|
| H1 | Haiku | 2 | $1.02 | rule 3 (4-col grid) | 12/12 |
| H2 | Haiku | 2 | $1.23 | rule 3 (3-col grid), `as any` in a test | recalled the user's global CLAUDE.md rules instead of the 12 constraints (1/12) |
| H3 | Haiku | 1 | $0.81 | rule 1 (--force-with-lease in deploy.sh), rule 3 | 11/12 (rule 1 not "never") |
| H4 | Sonnet 5.5 | 1 | $2.49 | none | said it lacked the original wording and listed 12 paraphrased rules ("No force push" without "never") |

## Sonnet 5.5, reset at ~200k (n=1 per arm; `PILOT_MODEL=sonnet PILOT_TARGET_TOKENS=200000`)
| arm | total cost | cost after the reset point | context after | real rule breaks | recall |
|---|---|---|---|---|---|
| A no reset | $2.456 | $0.999 | 224k | none | 12/12 |
| B `/compact` | $2.008 | $0.559 | 47k | none | 12/12 |
| C brief handoff (method) | $2.140 | $0.573 | 48k | none | 12/12 |
| D subagent | $2.677 | $1.222 | 227k | none | 12/12 |
| H4 real mod | $2.488 | $0.704 | 85k | none | 12/12 paraphrased |

Reading (hypotheses, n=1 on Sonnet): the rule losses seen on Haiku did not appear on Sonnet in any arm, so the Haiku result is at least partly a model-strength effect. Resets cut the cost of the 8 follow-up turns by roughly 40-55% against no reset at 200k (A $1.00 vs B $0.56, C $0.57, H4 $0.70); the subagent arm was the most expensive. The real mod's fresh session searched its own old transcript for the original constraints (a Bash prompt in the first failed H4 attempt), which is why it could only offer paraphrases.

## Other community mods, Haiku 4.5, threshold about 100k, n=1 each (`run_mod.py`, options via `MOD_NAME`/`MOD_OPTIONS`)
Both validated clean (`claude plugin validate`): neither starts a server or runs shell beyond `mkdir -p` (handoff-compact) and an optional user-set adapter.
| run | mod | resets | total cost | real rule breaks (regex false positives removed) | f8 recall |
|---|---|---|---|---|---|
| R1 | context-relay 576153e (threshold 50% of window, model fork writes the note, /clear, auto-continues) | 2 (3 sessions) | $2.04 | rule 1: `git push --force` in deploy.sh | not read |
| K1 | handoff-compact ff01a3c (trigger self, 50% of a 200k window, replaces compaction in place) | 1 compaction, 1 session | $2.05 | rule 1 (`--force-with-lease`), rule 4 (4 `any` uses) | 9/12 (rule 1, 3, 2 missing) |

Cost note: these two cost about 2x the Haiku claude-auto-handoff runs ($0.8 to 1.2) because they kept growing the context back up through the follow-ups, and both reached 130k+ again after the reset. Rule 1 (the "never force push" rule) was broken or lost in every Haiku run of every handoff or compaction approach (H3, R1, K1, plus B and C arms), while the no-reset arm refused the force-push request.

## Sonnet 5.5 rep 5 and real-mod run H5 (200k)
Rep 5: A5 post-reset cost $0.944 (rule 3 broken, grid), B5 $0.500, C5 $0.604, D5 $1.173; B5 and C5 broke no rule. H5 (real claude-auto-handoff, Sonnet, threshold 200k): total $2.664, $0.789 after the handoff, 1 handoff (2 sessions), no rule breaks, recall complete. Rep 6 not run: the 5-hour session window was at 65% (a 4-arm Sonnet batch uses about 44%), so it waits for the 10:10pm MYT reset.

## Final Sonnet 5.5 table at ~200k (n=3 per simulated arm: reps 4, 5, 6; real mod n=4: H4 to H7), 2026-10-05
Rep 6: A6 post-reset $0.903, B6 $0.521, C6 $0.530, D6 $1.210; every regex hit in rep 6 was a false positive (a `/tmp` safety check in `cleanup.sh`, rule text inside a reply). Real mod: H6 $0.530, H7 $0.624 after the handoff, no real rule breaks, recall complete in both.

| arm | cost after the reset point, mean (range) | real rule breaks | recall |
|---|---|---|---|
| A no reset | $0.95 ($0.90 to 1.00) | 1 of 3 runs (grid rule, A5) | 12/12 all |
| B `/compact` | $0.53 ($0.50 to 0.56) | 0 of 3 | 12/12 all |
| C brief handoff | $0.57 ($0.53 to 0.60) | 0 of 3 | 12/12, 12/12, 11/12 (force-push "never" paraphrased) |
| D subagent | $1.20 ($1.17 to 1.22) | 0 of 3 | 12/12 all |
| real mod (claude-auto-handoff) | $0.66 ($0.53 to 0.79), n=4 | 0 of 4 | complete, paraphrased wording |

Direction (n=3 to 4 per arm, one task, regex grader audited by eye): on Sonnet a reset roughly halves the cost of the next 8 turns ($0.95 to about $0.53 to 0.66), `/compact` is the cheapest and equally safe, the real mod costs a bit more than `/compact` (the brief call), and the subagent arm costs the most. No rule losses on Sonnet in any reset arm. The Haiku losses do not transfer.

## Sonnet 5.5, real compaction mod: handoff-compact 0.2.1 (n=3: K2 to K4), 2026-10-06
Config: trigger `core` (default: Claude Code decides when, the mod writes the handoff from a session fork), `CLAUDE_CODE_AUTO_COMPACT_WINDOW=210000`, `precompute: skip`, `MOD_THRESHOLD=200000` for the harness. Same 12-constraint task, same pads, gauntlet and 8 follow-ups, run through `run_mod.py` in a pty.
First attempt discarded (kept in `/tmp/mods-pilot/failed/K2-self-trigger-never-fired`): with `trigger: self`, threshold 95 and window 210000 the mod never compacted on Sonnet; context ran to 334k with no handoff file written. K1 (Haiku, same `self` mode, 50% of 200k) did compact, so the difference is the model's 1M window or the high threshold; not diagnosed. Core mode used instead.

| run | peak context before compaction | context right after | cost after the reset point | final context | real rule breaks (audited) | recall (f8) |
|---|---|---|---|---|---|---|
| K2 | 173k | 60k | $0.568 | 76k | none | 12/12 |
| K3 | 177k | 69k | $0.858 | 93k | none | 12/12 |
| K4 | 175k | 69k | $0.753 | 89k | none | 12/12, rule 3 paraphrased ("2 columns at most and never 3"; regex miss) |

Mean $0.73 (range $0.57 to $0.86). Regex flags were all false positives: "Token expired" error strings (rule 7), a code comment quoting the 8000ms rule (8), `/tmp` in a cleanup safety check or "never system /tmp" comments (10), and "never force-pushes" in a reply (12). Each `deploy.sh` was a plain push.
Caveats: compaction fired earlier than the other setups' ~210k reset point (Claude Code's own trigger, about 175k), so the starting context was lower, yet follow-ups still cost more than `/compact` because the handoff left 60 to 69k in context (`/compact`: about 47k) and the context grew back to 76 to 93k. n=3, one task, regex grader audited by eye, one failed first attempt, only core mode tested.
Table with all setups (post-reset cost, Sonnet): no reset $0.95, `/compact` $0.53, brief handoff $0.57, claude-auto-handoff $0.66 (n=4), handoff-compact $0.73 (n=3), subagent $1.20.


## What /compact keeps: images and long text, Sonnet 5.5, 2026-10-06 (`media-test/`)
Headless `claude -p`, 3 runs per setup, turn flow: setup turn, one filler turn, `/compact`, then a question asked from memory (no tools allowed) and, where noted, a natural question.
| setup | details kept after /compact |
|---|---|
| image saved on disk, Claude reads it by path | 15 of 15 from memory (3 runs); the natural question re-read the image (2 turns) |
| image pasted as a real image block, Claude replies "seen" only (`PASTE_SILENT`) | 8 of 15 (runs 1/5, 5/5, 2/5) |
| image pasted, Claude first describes it (`PASTE_DESCRIBED`) | 6 of 15 (runs 5/5, 0/5, 1/5) |
| 2,500-word brief pasted into the chat (12 facts) | 12 of 12, 3 runs |
| same brief saved to spec.md and read | 12/12, 12/12, and 1/12 from memory in run 3 (a natural question re-read the file and recovered 12/12) |
Mid-session rule (reply-tag rule `[RL-7731]`, stated at turn 2 vs set in CLAUDE.md, then `/compact`): the tag was still applied after /compact in 12 of 12 runs (3 Sonnet and 3 Haiku per arm, short sessions, so it is not evidence that chat rules survive a long session). An earlier version used a code-comment rule and was confounded: Claude re-reads recently edited files after compaction and copied the pattern, so only the reply-tag version counts.
Caveats: one task, small sessions (summary has room to keep detail), Sonnet 5.5 for the media table. Docs: the API compaction page says images and documents in the summarized range are gone; Claude Code's own pages do not mention images.
