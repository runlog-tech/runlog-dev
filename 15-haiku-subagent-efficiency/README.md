# 15 - Haiku 5.5 as a Claude Code subagent (video 27)

Receipts for the RUNLOG video "One Line Cut My Haiku 5.5 Subagent Cost by 40% on Most Jobs". Every number in the video comes from the files here: 63 controlled runs (49 across the six small tasks, 14 on the chart workload), about $7.64 of API spend.

## What was tested
Six small tasks (T1 search, T2 summarize, T3 check, T4 write code, T5 digest, T6 big file) plus one chart-building workload (R1). A headless Sonnet 5.5 session handed each task, verbatim, to a `worker` subagent running Haiku 5.5. Conditions changed one setup lever at a time: effort level, a pasted 1,500-word background, a concise-output line, a short tools list, a ticket-style prompt, Karpathy's four principles, the Ponytail minimal-code text, and a stack of the best ones. The plan, with the conditions and the stop rules, was written before the first run: `PLAN.md`.

## Start here
- `RESULTS.md`: the tables and the findings, including what the data does not show.
- `PLAN.md`: the pre-registered plan and hypotheses.
- `receipts/<task>_<condition>/`: for each run, the `agent.md` it used, the exact `brief.txt`, the subagent's `report.txt`, and `usage.jsonl` (per-turn token counts). Chart runs also keep the `last_frame.png` they rendered.
- `briefs.py`, `run_round1.py`: the prompts and the runner that launched the runs. `karpathy_claude_md.txt` and `ponytail_instructions.txt` are the two instruction texts tested.
- `render_task/scaffold/`: the starting project for the chart workload.

## Cost, and what it covers
Costs are modeled from token counts at the published Haiku 5.5 price (`$0.10` and `$0.50` per million input and output tokens up to 100K prompt tokens, `$0.50` and `$2.50` above). The percentages in the video are the subagent's own cost. The calling Sonnet session made up most of the bill, and `RESULTS.md` has both columns.

## Limits
Most cells are one run. The chart workload has three runs per cell. Nothing here tests a Sonnet subagent, a project with a big `CLAUDE.md` and MCP tools, or whether the full stack beats Karpathy's rules (three runs cannot rank them).

## Redactions
The pasted-background briefs (`receipts/T*_L7/brief.txt`) were the channel's private project instructions. Sibling repo names and a local path were replaced with `(names redacted)` and `~/other-pipeline`, and `/home/invii` was shortened to `~` in logs. Nothing else was changed.
