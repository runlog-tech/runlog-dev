# 13 - Claude Code mods vs /compact (video 21)

Receipts for "Claude Code Mods Cost More Than /compact. I Tested It". Every number in the video comes from the files here.

## What was tested
One long coding session in headless `claude -p` (Sonnet 5.5): twelve project rules in turn 1, file reads until the context reached about 200K tokens (the reset point), then a feature request and eight follow-ups (one asks to force push, the last asks for the twelve rules back). Six setups: do nothing (A), built-in `/compact` (B), a brief handoff to a fresh session (C), a subagent (D), the community mod claude-auto-handoff 0.8.4 (H), and handoff-compact 0.2.1 (K).

Cost after the reset point, mean: A $0.95, B `/compact` $0.53, C $0.57, H $0.66 (4 runs), K $0.73 (3 runs), D $1.20. One task, 3 runs per setup, regex grader checked by eye. See `RESULTS.md` for the full tables, caveats, the Haiku batch and the side-effect notes.

## Layout
- `RESULTS.md` - the results log (same file as `scripts/claude-code-mods-audit/PILOT_RESULTS.md` in the private repo).
- `runs/<setup+rep>/` - `meter.jsonl` (cost ledger: context tokens, rate limits, cumulative cost per turn), `meta.json`, `new_files.json`, and `turns/*.json` (each turn's reply). A4-A6 no reset, B4-B6 `/compact`, C4-C6 brief handoff, D4-D6 subagent, H4-H7 claude-auto-handoff, K2-K4 handoff-compact.
- `runs-media/` - the follow-up tests: `mods-media-test` (image on disk, pasted brief, brief saved to a file, then `/compact`), `mods-paste-test` (image pasted as a real image block), `mods-midrule-test` (a rule stated mid-chat vs in CLAUDE.md). Each run has `summary.json` and its turns.
- `harness/` - `run_pilot.py`, `run_mod.py`, `grade.py`, `analyze.py`, the cost-measuring mod `context-meter/`, and `media-test/*.py`.

## Reproduce
`python3 harness/run_pilot.py B4` style runs expect the author's local paths for the pad files and the task template, so treat the harness as documentation of the exact prompts and flow rather than a one-command rerun.

## Caveats
Small n, one task, Sonnet 5.5 for the cost table, regex grading. Pasted-image and mid-chat-rule tests used short sessions. The mods are days old and change quickly.
