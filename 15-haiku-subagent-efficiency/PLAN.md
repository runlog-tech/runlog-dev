# Making a Haiku 5.5 subagent token-efficient: same objective, different levers (ROUND 1 PRE-REGISTERED 2026-10-17, nothing run)

User direction 2026-10-17: code-writing task included; tasks are what people usually hand to a Haiku subagent (summarize, search, check, write code); one round only (n=1 per cell), then review before deciding on more; Haiku at High effort by default (low is not a setting the user would use); a long brief is a lever to measure, not assume.

## Why
Haiku 5.5 is cheap enough to be the default subagent; planning and hard thinking stay with Sonnet or Opus. Keeping a subagent under 100K tokens is not a Claude Code setting, so it has to come from design and instructions. Above 100K Haiku 5.5 is still cheaper than Haiku 4.5 or Sonnet, so the question is efficiency, not a cap. If promising, the next video is workflows, agent teams, teammates. Price step and subagent sizes: `scripts/context-cost-100k/`, `scripts/orchestrator-pilot/`, `memory/current_state.md`.

## Question
For the same objective, which design levers make a Haiku 5.5 (High effort) subagent use fewer tokens and cost less without losing correctness?

## Tasks (ground truth scripted; exact briefs in `briefs.py`, committed before any run)
| Id | Task | Scored by |
|---|---|---|
| T1 search | every mention of `meter.jsonl` in `scripts/**/*.py` (29 mentions at the fixture commit) | precision and recall of `path:line`, count of made-up lines |
| T2 summarize | `scripts/autocompact-window-test/RESULTS.md` (about 1,200 words) | 8 must-have facts present (regex first pass, read by eye), numbers in the summary not found in the file |
| T3 check | every `scripts/*/upload-notes.md` (26 files): has a Primary title line, has a `## Tags` heading | per-folder exact match against a script |
| T4 write code | `slugify` + pytest tests from a written spec | 12 hidden cases, own tests pass, lines written |

## Conditions
| Id | Name | Change vs L0 |
|---|---|---|
| L0 | baseline | one-line brief; agent prompt "You are a worker subagent. Do the task and report back."; no `tools:` field (inherits every tool, as many people define agents); Haiku 5.5 High |
| L1 | concise | agent prompt adds "Be extremely concise. Sacrifice grammar for the sake of concision. Final answer first, no preamble, no recap." |
| L2 | narrow tools | explicit `tools:` (T1 to T3: Read, Grep, Glob; T4: Read, Write, Edit, Bash) |
| L3 | better brief | self-contained brief: exact scope, method, stop rule, return format |
| L4 | medium effort | `effort: medium` |
| L5 | combined | L1 + L2 + L3 at High |
| L6 | Ponytail text (T4 only) | L0 plus Ponytail's instruction text (`ponytail_instructions.txt`, extracted from its repo `hooks/ponytail-instructions.js`, commit 16352ac, not installed or executed: the plugin runs node hooks and writes under the home directory) |
| L7 | long brief | L3 plus about 1,500 words of project background pasted into the brief (this repo's `CLAUDE.md` and `docs/VOCABULARY_AND_TONE_RULES.md`), the "way long prompt" case |
| REF | Sonnet reference | L0 with Sonnet 5.5 medium as the subagent, once per task |
Runs: T1 to T3 x L0 to L5 and L7 = 21; T4 x L0 to L7 = 8; REF 4. Total 33, n=1 each.

## How a run works
A headless Sonnet 5.5 parent at low effort (`claude -p`) is told to call the Agent tool once with `subagent_type worker` and the brief verbatim, then reply `DONE`. The agent definition is written to `.claude/agents/worker.md` in an isolated working directory (a `git worktree` of this repo at the plan's commit with `CLAUDE.md`, `AGENTS.md`, `.claude/` and `memory/` removed, so no project instructions load; T4 gets an empty scratch directory). Haiku cost and tokens come from `modelUsage` in the result JSON; turns, first and peak context from the subagent transcript (same `summarize` logic as `scripts/_tools/runlog-guard/subagent_ledger.py`); the subagent's final message is the report that is scored. Parent cost is recorded separately and not charged to the lever. Runner: `run_round1.py`.

## Measures (fixed before running)
Haiku cost; Haiku output tokens; Haiku input + cache tokens; turns; first and peak context (over 100K or not); chars of the returned report; correctness score per task; wall time; parent cost.

## Hypotheses (written before data)
- H1: L2 cuts Haiku cost by at least 15% against L0 (smaller start).
- H2: L1 cuts output tokens by at least 30% but total cost by under 10% (input and cache reads dominate).
- H3: L3 cuts turns and cost the most on T1 and T3.
- H4: no lever changes correctness by more than one item (T2 fact, T3 folder, T1 mention) per task.
- H5: L4 is cheaper than L0 and loses correctness on T2 or T3.
- H6: L5 is the cheapest Haiku condition on every task with correctness held.
- H7: L7 costs more than L3 and does not improve correctness (the long brief is carried on every turn for nothing).
- H8: L6 writes fewer lines than L0 on T4 with the same hidden-case score.
n=1 per cell: a difference smaller than about 15% is within the noise we have seen between identical runs (for example the three W1000 runs differed by 15%); nothing is ranked from one round.

## Not claimed
Anything about workflows, agent teams or teammates; Sonnet or Opus as workers beyond the REF row; open-ended tasks; Ponytail as installed (only its instruction text); whether a subagent's cost generalizes to other repos.

## Stop rules
Total budget cap $10 (expected about $8 to $9: about $0.12 parent plus $0.05 to $0.25 Haiku per run); weekly meter at 86% or a 5h window above 65%: stop and report; no extra runs or reruns after seeing data; a run that errors is an incident, logged, not retried unless the runner itself failed.

## After round 1
Review the table with the user; decide whether to add rounds (n=3), change conditions, or move to workflows.

## Amendment 1 (2026-10-17, after the first 5 runs, before the next one; user direction)
Why: the first five runs (T1, a single grep) left the Haiku subagent at 14K to 31K context and under a cent, so the levers could not show an effect that matters. The user asked for use cases where a subagent ends up around 100K to 120K or more after a few rounds, because settings only make a difference at that size.
- New long-context tasks (briefs appended in `briefs.py`; existing text unchanged), same conditions L0 to L5, L7 and a Sonnet REF each:
  - T5 digest: for every `scripts/*/script.md` (22 files, about 303 KB, about 75K tokens if read in full) report the title and the status line. Scored per folder: title match, status match (truth from a script; 6 of the 22 have a status line, the rest must say `none`).
  - T6 big-file summary: summarize entries 31, 34, 35 and 36 of a 347 KB file (`notes/video_ideas.md`, a copy of `memory/video_ideas.md` placed in the fixture; about 87K tokens if read in full). Scored on 8 must-have facts (regex first pass, read by eye).
  Reading the whole input puts the subagent near or over 100K; a method instruction (grep, then read ranges) keeps it small.
- New derived metric `norm_cost`: Haiku 5.5 cost recomputed from the subagent transcript's per-turn token counts at Anthropic's listed prices (up to 100K: input $0.10, output $0.50, cache write $0.125, cache read $0.01 per million; over 100K: $0.50, $2.50, $0.625, $0.05), assuming a cold start (turn 1 prompt written to cache, each later turn reads the previous prompt and writes the new tokens), the tier chosen by the turn's prompt size. It removes the run-order cache effect seen in the first five runs (measured costs differed by cache state; recomputed T1 costs: L0 $0.0062, L1 $0.0060, L2 $0.0036, L3 $0.0062, L4 $0.0059, so only L2 differs). Measured cost stays in the table too. Also recorded: turns over 100K.
- Extra hypotheses (written before data; H1 to H8 unchanged):
  - H9: on T5 and T6 the baseline L0 reaches at least 100K peak context in at least one task.
  - H10: the conditions that tell the subagent how to read (L3, L5) stay under 60K on T5 and T6 and cost at least 50% less (`norm_cost`) than L0, with correctness within the noise (H4).
  - H11: L2 (narrow tools) alone does not stop whole-file reading, so it helps much less on T5 and T6 than on T1.
  - H12: L1 (concise prompt) changes `norm_cost` by under 10% on T5 and T6 (reading dominates).
  - H13: L7 (long brief) changes `norm_cost` by under 10% on T5 and T6.
- Run order: T5 and T6 first, then the rest of the original plan; the runner skips runs that exist. Budget cap stays $10 total (spent so far $0.47); expected additional spend about $5. The dispatcher run `T1_L5` was interrupted at the stop and is re-run.
- n=1 per cell still; nothing is ranked from one round.

## Amendment 2 (2026-10-17, after round 1; user direction: a complex render task at high, extra high effort; and a precise-prompt lever from the Karpathy CLAUDE.md)
Why: no round 1 subagent passed 48K tokens (RESULTS.md). The user asked for a more complex task, rendering with higher effort, and mentioned the viral "Karpathy" CLAUDE.md as a precise-prompt idea to learn from. A render task loops write, check, fix and render, which should run more turns and carry more context.
- Task R1 (render): in a copy of `render_task/scaffold/` (a minimal HyperFrames project, 1920x1080, 6 s, placeholder scene; `check` passes and a render takes about 8 s on this machine), replace the placeholder scene with an animated horizontal bar chart of four cost-per-context-token values (0 to 50K $0.051, 50 to 100K $0.068, 100 to 150K $0.197, 150 to 250K $0.153), run `check` until it passes, render to mp4. The loose brief (L0) and a precise brief with exact commands (L3) are in `briefs.py`. Scored by script: `check` passes after the run; an mp4 exists at 1920x1080 and about 6 s; the four values, four labels and the title are in `index.html`; the frame at 5.5 s is not blank. Chart quality is read by eye from the last frame.
- Part A (run now, n=1 each, loose brief, no `tools:` field, Haiku 5.5): effort `high`, `xhigh`, `max` (`E_high`, `E_xhigh`, `E_max`). The CLI accepted `--effort xhigh` and `max` for Haiku 5.5 without error (a test call on 2026-10-17); whether they change behavior is what the runs show. Budget $2.
- Part B (after the weekly meter resets 2026-10-19, user to confirm): at the best effort from Part A, narrow tools (`Read, Write, Edit, Bash, Glob`), the precise brief with the HyperFrames commands, Ponytail's text, the Karpathy-style principles text (the repo's `CLAUDE.md`, fetched and unmodified, not yet read by us), and the combination. A 100K to 120K peak is only a target; if no condition reaches it, that is the finding.
- Hypotheses for Part A (before data): H14: `xhigh` and `max` use more turns and a larger peak context than `high`; H15: they do not produce a better chart (the script score is the same or the pass rate is the same; judged by eye); H16: all three finish under 100K tokens.
- Stop rules: Part A budget $2; weekly meter 86% stops everything; no reruns after seeing data; a run that errors is logged, not retried unless the runner failed.

## Amendment 3 (2026-10-17, after Part A, before Part B; user direction)
- Stop rules changed by the user: the weekly-meter stop at 86% and the 5-hour 65% line are REMOVED, for this plan and for the runners (`run_pilot.py`, `run_mod.py`, `run_window.py`, `run_round1.py` now default to no meter stop). The budget cap is the only stop. Older plans keep their original text as history.
- Part B starts now (not after the 2026-10-19 reset). Budget cap $3. Baseline is the Part A `E_high` run (n=1; Part B conditions are each n=1 and compared with it).
- Conditions, all Haiku 5.5 at High on task R1:
  - `B_narrow`: `tools:` limited to `Read, Write, Edit, Bash, Glob`; loose brief.
  - `B_brief`: the precise brief with exact check and render commands and every visual requirement (`L3['R1']`); inherited tools.
  - `B_ponytail`: baseline plus Ponytail's instruction text in the agent prompt (`ponytail_instructions.txt`, commit 16352ac).
  - `B_karpathy`: baseline plus the Karpathy-style principles text in the agent prompt: the `CLAUDE.md` of `multica-ai/andrej-karpathy-skills` (fetched 2026-10-17, 358 words, saved unmodified as `karpathy_claude_md.txt`; read by us; a distillation by a third party, not written by Karpathy).
  - `B_combo`: narrow tools + precise brief + Karpathy text.
- Scorer additions (defined before the runs; applied to all R1 runs including Part A): count of distinct font sizes below 40px, minimum font size, highlight styling present, and the title and label checks made case and dash tolerant (the Part A strings were an en dash and different casing; one label check still reads 0 for `E_max` because its labels are built in script, by eye they are present). Proportional bars, the highlight and the stagger are read by eye from the last frame and the HTML.
- Hypotheses (before data): H17: `B_narrow` and `B_brief` each cut turns and `norm_cost` by at least 30% against `E_high`; H18: `B_karpathy` does not cut cost (its first principle says ask when unsure, which a subagent cannot do, and it adds about 370 words per turn) and may add turns; H19: `B_ponytail` writes a shorter `index.html` than `E_high` (101 lines) and is not clearly cheaper; H20: `B_combo` is the cheapest run and no Part B run passes 100K peak context (the baseline peaked at 66K); H21: the precise brief is the only lever that fixes the missed 40px text rule.
- Not claimed: anything about xhigh or max beyond Part A; any ranking from n=1 per cell.

## Amendment 4 (2026-10-17, after Part B, before the repeats; user: run it)
Why: Parts A and B are n=1 per cell. The two results the video would lean on are that a precise brief cuts a render subagent's turns and cost, and that the baseline is slower and dearer. Repeat those cells to see the spread.
- Runs: two more of each of `E_high` (loose brief, High), `B_brief` (precise brief) and `B_combo` (narrow tools + precise brief + Karpathy text) on task R1, named `<cond>_r2` and `<cond>_r3` (6 runs; the Part A and B runs count as the first of each, giving n=3 per cell). Same briefs, agent definitions, scorer and fixture as before; no condition is changed.
- Measures: as Part B (turns, peak context, `norm_cost`, output tokens, scripted R1 checks, fonts under 40px, HTML lines), reported as the three values per cell with min, median and max.
- Hypotheses (before data): H22: the median `norm_cost` of `B_brief` is at least 50% under `E_high`'s and `B_combo`'s at least 60% under, and every `B_brief` and `B_combo` run is cheaper than every `E_high` run; H23: `B_brief` and `B_combo` finish in 12 turns or fewer in every run, `E_high` in 15 or more; H24: no run passes 100K tokens.
- Budget: still under the total $10 cap (spent so far about $7; these six runs are expected to add about $1). No meter stop. No further runs after seeing the data.
