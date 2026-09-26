# grill-taste-skill benchmark plan

**Naming note (2026-09-24, after the 6-generation run completed)**: the
executed benchmark (`prompts/`, `benchmark_results/`) used the working
filename `SYSTEM_DESIGN.md` throughout, since that predates discovering
the real convention. Verified afterward: the actual established (if
`alpha`-stage) spec is `DESIGN.md`, from Google Labs
(`github.com/google-labs-code/design.md`). This doc and the skill itself
are updated to the real name going forward; the executed prompt/result
files keep their original filenames as an accurate historical record of
what was actually tested — the rename doesn't change any real number.

Follow-up to video 14 (`taste-skill-fact-check`). Real question: if a
project has its own `DESIGN.md`, does it conflict with
`taste-skill`, replace the need for it, or complement it? And is a
short, project-specific document actually more effective per token than
a generic 21,998-token ruleset?

Reuses video 14's exact 3 briefs and grading harness for direct
comparability. New arms only — Arms A/B/E's real data already exists in
`scripts/taste-skill-fact-check/benchmark_results/full/`.

## New arms

| Arm | Configuration | Prompt size |
|---|---|---|
| F | `DESIGN.md` only (no taste-skill) | ~150-250 tokens/brief |
| G | `DESIGN.md` + full `taste-skill` v2 (combined) | ~22,000+ tokens/brief |

Arm F tests the "replace" claim: does a short, project-specific document
outperform both the naked baseline (0/3 clean) and the generic lean
directive (0/3 clean) on its own.

Arm G tests the real "conflict" question directly: stack both and see
whether they reinforce (fewer defects than either alone) or clash
(e.g. taste-skill's generic palette rules override the project's real
brand color, or the two produce contradictory layout instructions the
model has to arbitrate).

## DESIGN.md per brief

Each is a real, concrete document as if the user had gone through the
`/grill-taste-skill` interview for that specific fictional product —
not a generic template. See `system_designs/<brief>.md`.

## Reused from video 14

- Test briefs (same user_prompt text, same product): `b2b_saas`
  (Litestream-S3), `portfolio` (ex-Google Raft engineer), `interactive_widget`
  (query latency heatmap).
- Grader: `eval_grader.py` (taste-skill's own 50-item ban list), copied
  unmodified from `scripts/taste-skill-fact-check/`.
- Same model/endpoint: Qwen3.6-27B-GGUF via Lemonade,
  `http://localhost:13305/api/v1/chat/completions`.
- Baseline comparison numbers (already real, from video 14, not rerun):
  naked 0/3 clean, taste-skill v2 5/8 clean (1/9 excluded, truncated),
  lean directive 0/3 clean.

## Important scope caveat (found 2026-09-24, after all 6 runs completed)

Arm G's system prompt was built by manually concatenating
`DESIGN.md` and `taste-skill`'s `SKILL.md` into one string before
the API call. A real Claude Code session doesn't do this automatically:
`taste-skill` only loads on its own trigger, and a file merely named
`DESIGN.md` is never auto-loaded just by existing in the repo --
it needs a `CLAUDE.md` pointer (the one file Claude Code does load every
session) to actually reach context.

This is not extra integration work layered on top of having the doc --
it's the only way the doc does anything at all. Nobody writes a design
doc on purpose and then doesn't reference it; an unwired
`DESIGN.md` is an incomplete setup, not a realistic alternative
one. `/grill-taste-skill`'s SKILL.md treats adding the `CLAUDE.md`
pointer as a mandatory last step of "having" the doc, not an optional
add-on. The script should frame Arm G as what a correctly-created
`DESIGN.md` looks like in practice, not as a bonus upgrade path.

## Arm I: DESIGN.md + lean directive (2026-09-25)

Real question: does the cheap combo (`DESIGN.md`, ~280-320 tokens, +
the real 129-token/4-constraint lean directive from video 14, ~410-448
tokens total) get close to `DESIGN.md` + full taste-skill (~22,300
tokens) at 1/50th the cost? Ran all 3 briefs (`ablation/*_arm_i_*`),
same model/grader/render pipeline.

| Brief | Defects | Renders? |
|---|---|---|
| b2b_saas | 9 (6 em-dash, 2 version-label, 1 grid) | Renders, looks polished, but a real "v0.3.12" version label is visibly baked into the UI |
| portfolio | 1 | **Crashes** — malformed JSX (`<SectionRule="selected work" />`) |
| interactive_widget | 1 | Renders clean — no functional bugs, best `interactive_widget` result across either video |

**Verdict: not a reliable replacement for full taste-skill.** It crashed
on portfolio, the same fragility class `DESIGN.md` alone showed (2/3
crash rate there vs. 1/3 here — better, not solved). But it's a real,
useful middle point: clearly more reliable than `DESIGN.md` alone, at a
small fraction of taste-skill's token cost, and on `interactive_widget`
it beat every other configuration tested in either video, functionality
included. Script framing: a real cost/reliability tradeoff, not a
"cheap thing works just as well" claim.

## Em-dash ablation — dropped from scope (2026-09-25)

Ran a follow-up ablation (n=3 per arm, `ablation/`) trying to isolate
whether `DESIGN.md`'s Voice section specifically caused the em-dash
compliance difference between taste-skill-alone (video 14) and combined
(Arm G). Result: weak and inconclusive (full-doc 3/3 clean, no-Voice 2/3
clean with one outlier) -- not strong enough to claim as a finding, and
not visually/design-relevant to the point of this video regardless.
User feedback, correctly: taste-skill is fundamentally about visual
design (no purple gradients, real layouts), and a multi-hour side-chase
into a text-formatting micro-rule isn't central enough to justify the
compute spent, independent of whether the result had been clean.
**Not used in the script.** Kept in `ablation/` as a real, honest record
of a thread that was investigated and correctly deprioritized, not
deleted to hide the detour.

## Status

**All real testing complete as of 2026-09-25.** 10 real generations
total across Arms F/G/I (6 + 3 + the em-dash ablation's 6, 15 generations
counting the ablation). Every result graded (`eval_grader.py`) and
rendered (`render_real_tsx.py`, real headless-Chrome), not just
text-scanned.

**Locked findings for the script:**
1. `DESIGN.md` alone is unsafe (2/3 briefs crashed on real bugs) — not a
   replacement for taste-skill.
2. `DESIGN.md` + full taste-skill (properly wired via `CLAUDE.md`) gave
   the cleanest results of either video (1/0/0 defects) — pair, don't
   replace. Caveat: one 0-defect result was functionally broken (flat
   heatmap) — a clean grader score isn't proof of correctness.
3. `DESIGN.md` + the cheap 4-line lean directive is a real middle
   ground — better than the doc alone, still crashed once (1/3), cannot
   be claimed equivalent to full taste-skill.
4. Em-dash ablation: investigated, inconclusive, correctly dropped from
   the script (see below) — a real example of over-chasing a
   non-central detail, worth naming as a lesson rather than hiding.
5. Real external corroboration: taste-skill's own GitHub issues (#106
   compliance, #92 token cost) independently confirm the same two
   problems this benchmark and video 14 both measured.

Next step: script drafting.
