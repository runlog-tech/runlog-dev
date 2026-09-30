# claude-compact-amnesia

The real benchmark behind RUNLOG's test of the "`/compact` gives Claude
Code amnesia" claim: 12 explicit project constraints, declared once in
turn 1, checked after real compactions across 5 headless sessions.

## Headline result

**59 / 60 constraint-checks held (98.3%)** across every real compaction,
up to 3 sequential compactions on the same session. The pre-registered
hypothesis going in (">50% negative-constraint failure") did not hold.
The one real miss: `billingExport.ts` lost its server-side Bearer-token
check after 2 compactions; the calling React component still sent the
header correctly. It didn't replicate on a deeper run (3 compactions,
same rule set), so it reads as ordinary run-to-run variance on one
under-reinforced check, not a systematic depth effect, though 5 runs is
too small to rule that out definitively.

| Run | Compactions | Real token drops | Score | Miss |
|---|---|---|---|---|
| rep1 | 1 | 49,745 to 10,002 | 12/12 | none |
| rep2 | 1 | (compact succeeded, resumed after a kill) | 12/12 | none |
| rep3 | 1 | (compact succeeded, resumed after a kill) | 12/12 | none |
| stress1 | 2 | 41,090 to 7,296, then 61,494 to 14,393 | 11/12 | `billingExport.ts` missing Bearer check |
| stress2 | 3 | 40,538 to 6,863, then 59,485 to 10,197, then 61,458 to 10,333 | 12/12 | none |

Full methodology, hypotheses, the gauntlet prompt, grading rubric, and
mechanism facts sourced from Anthropic's own docs are in
[`benchmark_plan.md`](benchmark_plan.md).

## What's here

- `benchmark_plan.md` — the full pre-registered methodology: the 12
  constraints, the session trajectory, the post-compaction "gauntlet"
  prompt used to bait each rule, the grading rubric, and the real
  results table above with sourcing.
- `run_rep.sh` — the real harness script. Runs one full rep: 6 setup
  turns via headless `claude -p` (not hand-pasted), a real `/compact`,
  then the gauntlet prompt, all against one session ID.
- `eval_grader.py` — an automated regex-based grader, included for
  transparency about what was tried and rejected as a grading method,
  **not something to trust as-is**. Its rules were never cross-checked
  against a real transcript. The 59/60 headline number came from manual
  `grep` audits of the generated files against each constraint, not
  from this script's output.

## What's not here

No raw session transcripts. The test ran in a scratch directory
(`/tmp/compact-amnesia-test/`), and that directory was already cleaned
up before these receipts were prepared for publication. What survives
is the real, logged `compactMetadata` token-drop numbers and the manual
audit results in the table above, not the original per-session `.jsonl`
logs. If that's a problem for reproducing this exact run, it is a real
gap, not one being talked around, and the honest fix is to run it again
yourself with the script below.

## Reproducing it yourself

1. Have the `claude` CLI installed and authenticated.
2. `mkdir -p /tmp/my-compact-test/rep1 && ./run_rep.sh /tmp/my-compact-test/rep1`
3. Read `transcript.txt` for the full session, or `gauntlet_output.txt`
   for just the post-compaction response.
4. Manually check the gauntlet output against each of the 12 constraints
   in `benchmark_plan.md` section 2 (recommended), or run
   `python3 eval_grader.py /tmp/my-compact-test/rep1/gauntlet_output.txt`
   for a rough automated pass (see the caveat above before trusting it).
5. Repeat for however many reps you want; edit the script to add more
   setup turns or a second/third `/compact` for a stress run like
   `stress1`/`stress2` above.
