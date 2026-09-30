# antigravity-context-mechanics

The real benchmark behind RUNLOG's test of how Google Antigravity
(`agy`, running Gemini 3.8 Flash) retains project rules across a long,
uncompacted session, run as the same 12-constraint gauntlet used in
[`10-claude-compact-amnesia`](../10-claude-compact-amnesia), driven
through Antigravity's headless `--print`/`--output-format json` mode,
not hand-pasted.

## Headline result

**12 / 12 constraint-checks held (100%) at Turn 24, 617,319 input
tokens** — the checkpoint used on screen, chosen because it lines up
with Claude Code's `autoCompactWindow: 700000` default for a fair,
apples-to-apples comparison at a similar token scale. CP-1 (Turn 10,
196,315 tokens) also held 12/12.

| Checkpoint | Turns | Input tokens (that turn) | Score |
|---|---|---|---|
| CP-1 (low-range overlap) | 10 | 196,315 | 12/12 |
| CP-2 (mid-scaling, on-screen number) | 24 | 617,319 | 12/12 |

Full methodology, the 12 constraints, the gauntlet prompt, and sourcing
are in [`benchmark_plan.md`](benchmark_plan.md).

## A run we chose not to publish, disclosed rather than hidden

A third checkpoint (CP-3/CP-4, continuing to Turn 40) was run. It is
**not included in this repo.** Its reported token count (1,448,801
input tokens at the Turn 40 gauntlet, and 1,298,820 at the prior Turn
39) exceeds Gemini 3.8 Flash's documented 1,048,576-token context
window, and we could not confirm why before publishing — see
`benchmark_plan.md` section 6C and `receipts/CLI_CONTEXT_PROTOCOL.md`
for what we checked. On manual grep audit, the generated code from that
run still showed 12/12 constraint retention, same as CP-1 and CP-2 —
but we're not comfortable publishing an unexplained token count as a
verified data point, so neither the receipt file nor the run script for
that checkpoint are here. If you reproduce this yourself and can
explain the discrepancy, we'd like to know.

## What's here

- `benchmark_plan.md` — the full methodology: the 12 constraints (same
  ones from the Claude Code test), the checkpoint protocol, the
  gauntlet prompts, and the real results with sourcing, including a
  note on the unpublished CP-3/CP-4 run above.
- `run_cp1.py`, `run_cp2.py` — the real harness scripts for the two
  published checkpoints. Each shells out to the real `agy` CLI
  (`--dangerously-skip-permissions --output-format json --model
  gemini-3.8-flash-medium`), not a simulation. `BASE_DIR` in each
  script is hardcoded to the machine this ran on; update it before
  reusing.
- `eval_grader.py` — an automated regex-based grader over the actual
  generated code files. Like its Claude Code counterpart, its rules
  were never cross-checked against a full real transcript before this
  run; treat its scores as a rough signal, not ground truth. The
  headline numbers above come from this grader's output cross-checked
  against manual review of the generated files, not the grader alone.
- `receipts/checkpoint_{1,2}_results.json` — full per-turn token usage
  and the grader's output for both published checkpoints, straight from
  `agy`'s own JSON responses.
- `receipts/checkpoint_{1,2}_context.txt` — **not** a verbatim
  `/context` command dump. `agy`'s `/context` is a TUI-only view and
  errors out in headless `--print` mode (see
  `receipts/CLI_CONTEXT_PROTOCOL.md` for the exact reproduction and
  error text). These `.txt` files are a summary we composed from the
  real JSON usage stats instead — the underlying numbers are real, but
  don't mistake the format for a captured terminal session.
- `receipts/CLI_CONTEXT_PROTOCOL.md` — documents the `/context`
  headless-mode limitation, the real JSON telemetry schema used
  instead, and the unresolved CP-3/CP-4 token-count investigation.

## Reproducing it yourself

1. Have the `agy` CLI (Google Antigravity) installed and authenticated.
2. Edit `BASE_DIR` in `run_cp1.py` and `run_cp2.py` to a working
   directory of your own.
3. `python3 run_cp1.py` for the low-range run (10 turns + gauntlet),
   `run_cp2.py` for mid-scaling (24 turns + gauntlet at turn 25).
4. Results land in `receipts/checkpoint_N_results.json`; generated code
   lands in `test_run/`.
5. If you want to push further (a CP-3/CP-4-style deep run), you're on
   your own past turn 25 — that's exactly the range where our own run
   produced the unexplained numbers above.
