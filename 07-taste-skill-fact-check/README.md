# taste-skill-fact-check

The real benchmark harness from RUNLOG's video fact-checking
[`Leonxlnx/taste-skill`](https://github.com/Leonxlnx/taste-skill)
("the Anti-Slop Frontend Framework for AI Agents"), a viral Claude Code
skill (MIT licensed) claiming to stop agents from generating generic
"AI slop" UI.

We ran a real 5-configuration x 3-brief matrix (15 generations) against
a local model (Qwen3.6-27B-GGUF, AMD RX 7900 XTX via Lemonade), graded
every output against the skill's own 50-item ban list, and measured
real time-to-first-token cost.

This isn't a redistribution of `taste-skill` itself — install the real
thing from its own repo if you want to try it. This is the tooling we
built to test it.

## What's here

- `scripts/run_full_benchmark.py` — runs the 15-generation matrix
  (5 arms x 3 briefs) against a local OpenAI-compatible chat completions
  endpoint, saves raw code + timing metadata per run.
- `scripts/eval_grader.py` — automated regex/AST-style grader that scans
  generated code against `taste-skill`'s own "Section 9: AI Tells" ban
  list (em-dashes, middle-dot spam, numbered eyebrows, version labels,
  3-column card grids, pure black, startup buzzwords, fake terminal
  mockups) and reports real motion-library usage (GSAP / Framer Motion /
  plain CSS transitions).
- `scripts/render_real_tsx.py` — renders the actual LLM-generated `.tsx`
  output in headless Chrome via native ES module imports (`esm.sh`) and
  Babel standalone for JSX/TS stripping only, so what you see is the
  real generated component, not a hand-typed mockup of what it might
  look like.
- `scripts/benchmark_plan.md` — the full experimental design: the 5 arms,
  the 3 test briefs and why each was chosen, and the grader schema.
- `scripts/lean_directive.md` — the real 4-line, 129-token alternative
  we benchmarked against `taste-skill`'s 21,998-token system prompt.

## The 5 arms

| Arm | Configuration | Prompt size |
|---|---|---|
| A | Naked, zero design guidance | 12 tokens |
| B | `taste-skill` v2, default dials | 21,998 tokens |
| C | `taste-skill` v2, low motion dial | 21,998 tokens |
| D | `taste-skill` v2, high motion dial | 21,998 tokens |
| E | Our lean directive (see `lean_directive.md`) | 129 tokens |

## Usage

Point `URL`/`MODEL` in `run_full_benchmark.py` at your own local or
hosted OpenAI-compatible chat completions endpoint, then:

```
python3 run_full_benchmark.py
python3 eval_grader.py benchmark_results/full/
```

## Real headline numbers from our run

- `taste-skill` v2 injects 21,998 exact tokens per turn (measured with
  `cl100k_base`, not estimated).
- Real average time-to-first-token: 2.02s naked vs. 2.99s skill-loaded
  (~1.5x slower, not the "56-second freeze" some viral takes claimed).
- Against the skill's own 50-ban checklist: skill-loaded arms landed at
  5/8 clean (1 of 9 generations excluded as a documented truncation gap);
  naked was 0/3 clean; our 129-token lean directive was also 0/3 clean.
  A real, measurable improvement over doing nothing, not immunity — a
  3-column-grid violation slipped through in every arm type tested.
- The skill's `MOTION_INTENSITY` dial didn't produce the claimed effect:
  GSAP/ScrollTrigger appeared in 0 of 15 generations at any setting.

Limits: one local model, 3 briefs, single runs per cell. These are
results for this setup, not a verdict on every model or every
`taste-skill` variant.
