# 14 - Opus 5.5 effort on one visual task (video 25)

Receipts for the RUNLOG video on one render task done by five model and effort setups. Every number in the video comes from the files here. The X post that prompted it (Opus 5.5 on "light" effort, 2+ hours, 35% of the 5 hour limit) was not tested.

## What was tested
One task: build one section of an earlier video (Result one, the bill, from the handoff mods video) as a single HyperFrames frame at 1920x1080 and render it. Every setup got the same finished script, the same voice recording of that script and the same design document. Headless `claude -p`, Claude Code 2.1.290 and 2.1.291, Pro plan. Setups: Opus 5.5 high, medium, low and Sonnet 5.5 high, medium (set with `--effort`). One run each in the final round (round 3b).

## Results (round 3b, one run per setup)
| Setup | Turns | Output tokens | Cost | 5h meter |
|---|---|---|---|---|
| Opus 5.5 high | 34 | 39,305 | $2.28 | 38 to 50 |
| Opus 5.5 medium | 40 | 23,366 | $1.71 | 51 to 60 |
| Sonnet 5.5 high | 37 | 35,893 | $1.28 | 65 to 73 |
| Opus 5.5 low | 9 | 9,025 | $0.64 | 61 to 65 |
| Sonnet 5.5 medium | 15 | 11,317 | $0.45 | 73 to 76 |

Full table with thinking tokens, cache reads and rounds 1 to 3: `results.md`. Most counted tokens were cache reads (2.78M for Opus high, about 95%), so a large token count mostly says how many turns re-read the same context.

## What it does and does not show
For this one visual task, in these runs, Opus high looked best to me and Sonnet high second. That is a judgment from watching the renders, not a measured rule. The script that won the earlier rounds was also written by Opus high, which is a confound. One task, one run per setup, a usage meter that moves in whole points from a different start each run. The earlier rounds changed more than the model (own scripts, a frame builder tool, two sections), so their costs are not comparable to round 3b.

## Files
- `results.md`, `facts.json`: the numbers, extracted by `harness/facts.py` from the run logs.
- `round3b_prompt.txt`: the exact prompt every setup got in round 3b.
- `runs/<round>/<setup>/`: `meta.json` (model, effort, meter before), `meter.jsonl` (cost and usage readings), `summary.json`, `script.md`, and `frames/` (the HTML frame each setup wrote). Full transcripts and rendered video are not included.
- `harness/`: the scripts that launched the runs (`run_build.py`, `run_frames.py`) and the per-round briefs (`HOUSE_RULES*.md`). The channel's private design document is not included; the briefs name it.
