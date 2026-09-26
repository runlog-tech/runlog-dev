# grill-taste-skill

The real DESIGN.md test harness from RUNLOG's follow-up to
[`taste-skill-fact-check`](../07-taste-skill-fact-check): does a
project's own design doc ([google-labs-code/design.md](https://github.com/google-labs-code/design.md))
replace [`Leonxlnx/taste-skill`](https://github.com/Leonxlnx/taste-skill),
or do they need to be paired?

We ran a real 3-configuration x 3-brief matrix (9 generations) against
a local model (Qwen3.6-27B-GGUF, AMD RX 7900 XTX via Lemonade), graded
every output against `taste-skill`'s own 50-item ban list, and checked
whether each one actually built and rendered.

This isn't a redistribution of `taste-skill` or `DESIGN.md` itself —
install the real things from their own repos if you want to try them.
This is the tooling we built to test them together.

## What's here

- `run_benchmark.py` — runs the DESIGN.md-alone and DESIGN.md+taste-skill
  matrix against a local OpenAI-compatible chat completions endpoint,
  saves raw code + timing metadata per run.
- `ablation/run_ablation.py` — runs the third setup (DESIGN.md + a cheap
  4-line lean directive, no full skill) as a follow-up ablation pass.
- `eval_grader.py` — automated regex/AST-style grader that scans
  generated code against `taste-skill`'s own "Section 9: AI Tells" ban
  list, same as the fact-check video's grader.
- `render_real_tsx.py` — renders the actual LLM-generated `.tsx` output
  in headless Chrome via native ES module imports and Babel standalone,
  so what you see is the real generated component.
- `benchmark_plan.md` — the full experimental design: the 3 setups, the
  3 test briefs, and the grader schema.
- `system_designs/` — the 3 real `DESIGN.md` files we wrote and tested
  (`b2b_saas.md`, `portfolio.md`, `interactive_widget.md`), each with
  its own palette, layout, motion, and voice rules.
- `prompts/` — the exact system prompts sent per brief x setup
  combination, as actually dispatched to the model.

## The 3 setups

| Setup | Configuration | Prompt size |
|---|---|---|
| 1 | `DESIGN.md` alone, no `taste-skill` | ~300 tokens |
| 2 | `DESIGN.md` + `taste-skill`, both loaded | ~22,300 tokens |
| 3 | `DESIGN.md` + a cheap 4-line lean directive instead of the full skill | ~410-448 tokens |

## Usage

Point `URL`/`MODEL` in `run_benchmark.py` at your own local or hosted
OpenAI-compatible chat completions endpoint, then:

```
python3 run_benchmark.py
python3 ablation/run_ablation.py
python3 eval_grader.py benchmark_results/
```

## Real headline numbers from our run

- Setup 1 (`DESIGN.md` alone): 2 of 3 briefs crashed with real runtime
  errors, not style complaints — a `ReferenceError: S3_BUCKET is not
  defined` in the B2B SaaS brief, and an unclosed JSX tag in the
  portfolio brief. A short design doc has nothing to say about whether
  the code actually runs.
- Setup 2 (`DESIGN.md` + `taste-skill`): the cleanest result across
  both this video and the fact-check video — 1 defect, 0, 0 on the
  same three briefs that crashed twice with the doc alone. This only
  holds once `DESIGN.md` is actually wired into `CLAUDE.md` — Claude
  Code doesn't auto-scan a repo for a file with that name.
- Setup 3 (`DESIGN.md` + the lean directive): a real middle ground, not
  equivalent to the full skill. The portfolio brief crashed again (same
  failure class as setup 1), the B2B SaaS brief rendered but shipped 9
  defects including a baked-in version label and the same 3-column grid
  pattern that showed up in every setup tested across both videos, and
  the interactive widget brief came back clean.

Limits: one local model, 3 briefs, mostly single runs per cell. These
are results for this setup, not a verdict on every model or every
design-doc format. Independently corroborated by `Leonxlnx/taste-skill`
GitHub issues [#106](https://github.com/Leonxlnx/taste-skill/issues/106)
(compliance enforcement) and [#92](https://github.com/Leonxlnx/taste-skill/issues/92)
(token cost).
