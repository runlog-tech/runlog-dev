# What survives compaction: Antigravity (agy) vs Claude Code

Retest receipts for RUNLOG video 19. Run 2026-10-03.

## Status of the earlier version

The first version of this experiment (video 18, now private) is withdrawn. Its files are kept unchanged in `withdrawn-v1/` for history only. Do not cite them. Why:

- It claimed Antigravity does not compact. It does: agy compacts on its own at about 130K tokens of context per model call (below).
- Its "617,319 tokens in context" figure was not a context size. `result.usage` in `agy --output-format stream-json` is cumulative over the whole conversation. Per-call context is on each `agent_response` step.
- Its KB figures and the "12/12" score had no receipt behind them. This retest replaces them.

## What was run

Same protocol, both tools, n=3 each, plus one no-compaction control per tool.

| | Antigravity | Claude Code |
|---|---|---|
| CLI | `agy` 1.2.15 (CLI logs show it auto-updated from 1.2.14 before these runs) | `claude -p` |
| Model | gemini-3.8-flash-medium | haiku |
| Compaction | automatic, at about 130K per call | manual `/compact` at about 135K per call |
| File rule lives in | `AGENTS.md` | `CLAUDE.md` |

Caveats that matter:

- The models are a same-class pair, not the same model.
- Claude's compaction was triggered by hand at the same context size agy compacts at. Claude's own automatic threshold is much higher.
- The user's global `CLAUDE.md` was loaded in the Claude workspaces (about 23K tokens of baseline context).
- agy compacted by itself in the middle of filler turn F10 (after 10 specs read, from a base of about 12.7K tokens). Claude started from about 23K tokens of baseline, was compacted by hand between turns after 8 specs, so the two histories differ.
- The probe told both tools to answer from memory with no tools. Claude obeyed and said it did not have the detail. agy used no tools on the five memory probes except in rep 2, where it re-read the spec file (3 tool calls) for M6. (The sixth probe writes a file by design.) That run is scored `Y*` and kept out of the "from memory" count.
- In Claude rep 3, Haiku did not write the `CLAUDE.md` header on its three feature files before compaction (the baseline check failed), although `src/util/sum.ts` written after compaction had it. So that run does not show the rule "holding through" compaction; the other five runs do.
- Sample size is 3 per tool. One incidental detail separates the tools. Read it as a pattern in this setup, not a general verdict.

## Protocol

Setup turn, three feature turns, then filler turns that each read a ~69 KB spec file in full, until the context is past the compaction point, then two more filler turns, then one probe per marker. Probes ask from memory ("do not open any file or run any command"). A probe that used tools is flagged `*` in the table.

Markers: M1 rule in the prompt only (no lodash, exported functions start `rl_`); M2 rule in the instruction file only (first line of new TypeScript files is an exact header); M3 code shown once in an image; M4 constant in a JSON file read once; M4B second constant in the same file (incidental); M5 order of the first three files created; M6 a sentence buried in section 7 of a spec file (incidental).

## Results

See `results.md` for the full table and per-run numbers.

| Marker | agy (3 runs) | Claude Code (3 runs) |
|---|---|---|
| M1 prompt rule | 3/3 | 3/3 |
| M2 file rule | 3/3 | 3/3 post-compaction; in 1 run the rule was also ignored before compaction, so 2/3 are clean |
| M3 image code | 3/3 | 3/3 (one answer hedged) |
| M4 limit constant | 3/3 | 3/3 |
| M4B pool size | 3/3 | 3/3 |
| M5 file order | 3/3 | 3/3 |
| M6 buried sentence | 2/3 from memory, 1/3 by re-reading the file | 0/3 |

Both controls (short run, no compaction) passed M1 to M5. They never read the spec file that holds M6, so M6 is not tested in the controls. The controls show the other markers are retained without compaction; they say nothing about M6 baseline retention.

## Compaction artifacts

- agy writes a `checkpoint` step into the conversation transcript (`compaction-summaries/agy-rep*-checkpoint.md`). The per-call context drops from about 130K to about 14.5K at that step. The summary lists the user requests, setup values, files created and key findings. The rep 1 and 3 summaries contain the buried paging threshold. The rep 2 summary does not, and in that run the agent re-read the spec file (3 tool calls) to answer.
- Claude's `/compact` summary (`compaction-summaries/claude-rep*-compact-summary.md`) kept the image code, constants and file order but not the buried sentence in any run. `compact_boundary` metadata: pre_tokens 137,800 / 136,304 / 134,563, post_tokens 3,930 / 3,946 / 4,077. Context afterwards sits near 25K, which is the baseline.
- Neither tool's M2 result can be credited to its summary alone: the Claude rep 1 and 2 summaries mention the header, the rep 3 summary does not. The instruction file is also loaded at the start of each resumed run, so a compliant post-compaction answer does not prove the summary carried the rule.

## Files

- `protocol/` the workspace generator, prompts, scorer and the two runners
- `runs/<tool>-rep<N>/` raw stream-json per turn plus `state.json` (answers, per-call context curve, auto scores, ground truth)
- `compaction-summaries/` the compaction text from each run
- `results.md` scored table

Scores are automatic (substring and rule checks) and were hand-audited against `state.json` answers.
