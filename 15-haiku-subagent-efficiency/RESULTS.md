# Haiku 5.5 subagent efficiency, round 1 (run 2026-10-17, plan and Amendment 1 in PLAN.md, n=1 per cell, direction only)

49 runs: 6 tasks x conditions L0 to L5 and L7 (T4 also L6) plus a Sonnet reference per task. A headless Sonnet 5.5 parent handed each task verbatim to a defined `worker` subagent (Haiku 5.5, High effort unless the condition says medium). Receipts: `receipts/results.jsonl` (one row per run), `receipts/<task>_<cond>/` (brief, agent definition, report, per-turn usage). Spend $5.71, weekly meter 82% at the end. The fixture at the plan commit has 34 `meter.jsonl` mentions (T1) and 22 `upload-notes.md` files (T3), not the 29 and 26 estimated in the plan.

## Haiku subagent cost, as a change against the baseline L0 (`norm_cost`, cold-start cost from token counts at Anthropic's prices)
| Condition | T1 search | T2 summarize | T3 check | T4 code | T5 digest | T6 big file |
|---|---|---|---|---|---|---|
| L1 concise prompt | -4% | -1% | -30% | +1% | -3% | -23% |
| L2 narrow tools | -41% | -49% | -54% | -40% | +35% | -49% |
| L3 better brief | -1% | +12% | -53% | -1% | -30% | -10% |
| L4 medium effort | -5% | -2% | -41% | -7% | -20% | -18% |
| L5 combined (L1+L2+L3) | -47% | -45% | -74% | -56% | -57% | -45% |
| L6 Ponytail text (T4 only) | | | | -8% | | |
| L7 long brief (1,500 words) | +9% | +30% | -53% | +13% | +2% | +25% |
| L0 baseline, `norm_cost` | $0.0062 | $0.0053 | $0.0149 | $0.0075 | $0.0127 | $0.0086 |

Haiku subagent cost per run was $0.002 to $0.017. The measured cost differs from `norm_cost` mainly by cache state from the previous run (the same shape of prompt costs less when it was cached a minute earlier); `norm_cost` removes that.

## What stood out
1. No Haiku subagent reached 100K tokens. Peaks: 12K to 48K in every run, including the baseline on the two long tasks (T5 reads 22 files totalling about 75K tokens, T6 a 347 KB file of about 87K tokens): Haiku searched and read ranges instead of reading everything. The case of a subagent around 100K to 120K did not occur on realistic one-shot delegations. A plain loose brief on a 87K-token file peaked at 38K.
2. The biggest single lever is a narrow `tools:` list: the start context falls from about 25K to about 10K tokens (62% less), and cost 40% to 54% on five of six tasks. The exception is T5 (+35%): with a loose brief and no way to run a command, the narrow-tools subagent took 34 turns and 12.8K output tokens instead of 13 turns.
3. Combined (L5) was 45% to 74% cheaper than baseline on all six tasks and cheapest on four of six; on T2 and T6 narrow tools alone was marginally cheaper (-49% vs -45%).
4. A better brief mainly cuts turns where the baseline wanders: T3 18 turns to 7 (-53% cost), T5 13 to 7 (-30%). Where the baseline already finished in 3 to 4 turns (T1, T2, T4) it changed nothing.
5. The concise-output line and medium effort did little in a consistent direction: L1 -30% on T3 and -23% on T6, near zero elsewhere; output tokens moved from -52% (T3) to +58% (T2). In the one baseline run I checked (T1), about 75% of the output tokens were not in the visible report (likely thinking, not stored in the transcript), which wording cannot touch.
6. The long brief (L7) raised Haiku `norm_cost` against the same brief without the background (L3) by +10%, +16%, +2%, +14%, +46%, +39%, and raised the Sonnet parent's cost by $0.06 to $0.14 per run, because the parent has to write it out and carry it. The answer to "is a very long prompt expected to be cheap": it is cheap per turn for Haiku (cache reads) and not free; the delegating model pays most of it.
7. Ponytail's instruction text on the code task (L6): 41 lines written against 84 (-51%), hidden-case score 12 of 12 for both, Haiku cost -8%. A brief that gives a return format and stop rule (L5) also cut code to 44 lines. All nine T4 runs passed 12 of 12 hidden cases.
8. The dispatcher dominates the bill: the Sonnet parent cost $0.02 to $0.24 per run against $0.003 to $0.017 for the Haiku subagent. A one-grep task costs more to delegate than to do. (Parent costs also swing with the parent's own cache state, so only the large L7 gap is clearly the lever.)

## Correctness
- T1: every run found all 34 mentions, none made up. T4: all 12 of 12. T2: 8 of 8 facts for most, 7 of 8 for L1 and L5.
- T6: L3 and L5 had 6 of 8 facts (the brief caps the summary at 10 bullets for four entries), L7 7 of 8, others 8 of 8 (regex first pass).
- T3 and T5: the loose brief does not define the check, so those runs answered a differently defined question rather than a wrong one: for T3 the baseline Haiku said 21 of 22 files fail a literal "Primary title" check and then a looser check, the Sonnet reference counted 21 as failing, the defined check (L3, L5, L7) found 17 failing and matched the script for all 22 folders. The scorer only credits output in the defined format, so L0, L1, L2, L4 and REF score 0 of 22 on T3 and low on T5 by format. A vague brief changes the answer, not just the cost; that is a finding, but the exact-match numbers for loose briefs are not a measure of Haiku's accuracy.

## Against the pre-registered hypotheses
- H1 (L2 cuts cost at least 15%): true on five of six tasks, false on T5.
- H2 (L1: output -30%, cost under 10%): not supported; effects are mixed.
- H3 (L3 helps most on T1 and T3): true for T3, not T1.
- H4 (correctness within one item): true except T6 (L3 and L5 6 of 8).
- H5 (L4 cheaper, loses correctness on T2 or T3): cheaper on all tasks (-2% to -41%); no loss measured on T2; T3 not comparable.
- H6 (L5 cheapest on every task): four of six.
- H7 (L7 costs more than L3 and is no better): true on cost, nothing gained.
- H8 (L6 fewer lines, same score): true.
- H9 (L0 reaches 100K on at least one long task): false, the largest baseline peak was 46K.
- H10 (L3 and L5 under 60K, at least 50% cheaper on T5 and T6): under 60K yes; at least 50% cheaper only L5 on T5 (-57%), T6 -45%.
- H11 (L2 helps much less on T5 and T6): mixed (T5 +35%, T6 -49%).
- H12 (L1 under 10% on T5 and T6): T5 yes (-3%), T6 no (-23%).
- H13 (L7 under 10%): false against L3 (+46% and +39% on T5 and T6).

## Limits
- n=1 per cell; differences under about 15% are within what identical runs vary by in our earlier tests. Rule of thumb for reading the table: only narrow tools (L2), the combination (L5) and the long-brief increase (L7) are larger than that, consistently.
- The Sonnet reference rows cannot show the Sonnet subagent's own cost: parent and subagent are the same model, so the result file merges them. Do not compare REF cost with Haiku cost. Sizes and correctness in those rows are valid.
- `norm_cost` is a model of the bill (cold start, tier by prompt size), not an invoice.
- Tasks are small repo tasks run through a headless dispatcher in a fixture without project instructions; results may not carry over to other repos or an interactive session.
- The context range the user asked about (100K to 120K) was not reached; any claim about subagents near the 100K price line from this round would be unsupported.

## Part A of Amendment 2: the render task at three effort levels (run 2026-10-17, n=1 each, loose brief, Haiku 5.5, no `tools:` field)
Task R1: replace a placeholder HyperFrames scene with an animated bar chart of four values, run `check` until it passes, render to mp4. Receipts: `receipts/R1_E_*` (final `index.html`, last frame, report, per-turn usage).

| Effort | Turns | Peak context | Turns over 100K | Output tokens | `norm_cost` | Measured Haiku cost | Wall time |
|---|---|---|---|---|---|---|---|
| high | 25 | 66K | 0 | 16.4K | $0.028 | $0.021 | 117 s |
| xhigh | 35 | 99K | 0 | 38.0K | $0.053 | $0.042 | 215 s |
| max | 54 | 210K | 30 | 98.7K | $0.510 | $0.355 | 504 s |

- All three passed `check`, rendered a 1920x1080, 6.0 s mp4, and had the four values and a title of 84px in the HTML. This is the first task in which a subagent crossed 100K: only the `max` run, and it spent 30 of its 54 turns over the line.
- The tier effect in that run (model, not an invoice): 93% of its `norm_cost` ($0.473 of $0.510) came from the 30 turns over 100K; the same tokens at the up-to-100K price would be $0.132, 26% of the modeled cost.
- Quality, read by eye from the last frames. CORRECTION 2026-10-17: an earlier version of this section scored these runs against rules that are only in the precise brief (a highlighted bar, all text at least 40px). The loose brief given to these three runs asked for none of that ("make it look good"), so those are not misses. What the loose brief asked for: an animated bar chart of the four values, `check` passing, an mp4. All three delivered that.
  - high: rich style (gradient bars, an orange highlight and a HIGHEST tag nobody asked for, axis ticks), bars proportional.
  - xhigh: bars proportional, a light-blue glow on the 100 to 150K bar and a PEAK tag, axis ticks.
  - max: bars proportional but thin and one color, the least decorated of the three.
  - So the extra effort bought no visible improvement at n=1; it did not make the result worse against what was asked.
- Against the pre-registered guesses: H14 true (more turns and a larger peak with each level); H15 supported at n=1 (no better chart at a higher level; `max` was the plainest); H16 false (`max` reached 210K).
- Reading: at n=1, `xhigh` cost about 1.9x and `max` about 18x what `high` did (`norm_cost`) for no visible gain. This is one task and one run per level; it is not a ranking of the levels. Part B (levers at `high`: narrow tools, precise brief, Ponytail text, Karpathy-style principles text, combination) is waiting for the weekly meter reset on 2026-10-19.

## Part B of Amendment 3: levers at High on the same render task (run 2026-10-17, n=1 each; baseline is the Part A `E_high` run)
Receipts: `receipts/R1_B_*`. Two conditions changed what was asked (the precise brief adds explicit requirements: exact labels, a highlighted bar, all text at least 40px, the exact check and render commands); the others change only the agent prompt or tools.

| Condition | Turns | Start ctx | Peak ctx | Output tokens | `norm_cost` | vs `E_high` | HTML lines | Fonts under 40px | Highlight |
|---|---|---|---|---|---|---|---|---|---|
| E_high (baseline) | 25 | 20.3K | 66K | 16.4K | $0.0278 | | 101 | 4 sizes | yes (unasked) |
| B_narrow (tools) | 39 | 6.1K | 37K | 18.5K | $0.0228 | -18% | 103 | 2 | yes |
| B_brief (precise brief) | 9 | 20.6K | 40K | 5.2K | $0.0097 | -65% | 57 | 0 | yes |
| B_ponytail (text) | 20 | 21.1K | 46K | 9.4K | $0.0168 | -40% | 62 | 1 | yes |
| B_karpathy (text) | 30 | 21.2K | 64K | 9.4K | $0.0260 | -6% | 76 | 2 | yes |
| B_combo (tools + brief + Karpathy) | 9 | 7.2K | 25K | 4.9K | $0.0066 | -76% | 53 | 0 | yes |

All five passed `check` and rendered a 1920x1080, 6 s mp4 with the four values. No Part B run passed 66K tokens; the baseline's 66K is the highest of the six. By eye: `B_combo` and `B_brief` are flat and follow the brief exactly (title in capitals, labels `0 to 50K` and so on, an orange bar, 44px text); `B_ponytail` is polished pill bars with a gold highlight; `B_karpathy` dims the other bars and values to gray (gray text on the dark background, which the house rules forbid; the loose brief did not say so).

- The big lever is a brief that says how to work: 25 turns down to 9, output tokens a third, cost -65%. It also gives a plainer result: with room to "make it look good" the subagent iterated on polish; with an exact spec it wrote the file once, checked and rendered.
- Narrow tools alone cut the start context from 20K to 6K but made the subagent take 14 more turns (39), so cost fell only 18%. With the precise brief on top (`B_combo`) the turns stayed at 9 and cost fell to a quarter of baseline.
- Ponytail's text roughly halved the lines written (62 vs 101) and cut turns from 25 to 20 (-40% cost). Karpathy's text did little (-6%, 30 turns, 76 lines); its first principle says to ask when unsure, which a subagent cannot do.
- Against the pre-registered guesses: H17 false for `B_narrow` (-18%) and true for `B_brief` (-65%); H18 true (no real saving from the Karpathy text); H19 half true (shorter HTML, but also -40% cost); H20 true (`B_combo` cheapest, nothing over 100K); H21 true but confounded: only the precise brief asked for 40px text, so it is not evidence about what a prompt can fix.

## Limits (Part A and B)
- n=1 per cell; one task; Haiku 5.5; the render ran on this machine in 8 s, so the render loop is cheap here.
- The spec differs between the loose and precise briefs, so quality comparisons across them are not like for like; cost and turns are real.
- 100K to 120K was reached only by `max` effort (210K). At High, with or without any lever, a render subagent stayed under 70K.

## Round 3 (Amendment 4): the key render cells repeated, n=3 per cell (run 2026-10-17)
`E_high` (loose brief), `B_brief` (precise brief) and `B_combo` (narrow tools + precise brief + Karpathy text); the Part A and B runs are the first of each. Receipts: `receipts/R1_*_r2`, `*_r3`. Spend for the six repeats about $0.7 (total about $7.7 of the $10 cap).

| Cell | Runs | Turns | Peak context | Output tokens | `norm_cost` (min / median / max) | HTML lines |
|---|---|---|---|---|---|---|
| E_high | 3 | 25, 30, 34 | 60K to 71K | 11K to 16K | $0.0257 / $0.0278 / $0.0286 | 101 to 132 |
| B_brief | 3 | 9, 10, 14 | 32K to 41K | 4.5K to 5.2K | $0.0086 / $0.0097 / $0.0111 | 54 to 66 |
| B_combo | 3 | 9, 15, 18 | 20K to 28K | 4.9K to 6.2K | $0.0066 / $0.0076 / $0.0086 | 51 to 57 |

- Against the baseline median: `B_brief` -65%, `B_combo` -73%. Every `B_brief` and `B_combo` run was cheaper than every `E_high` run (the highest of them, $0.0111, is 57% under the baseline's lowest, $0.0257).
- All nine runs passed `check`, rendered a 1920x1080 6 s mp4, and had the four values, labels and title. Every `B_brief` and `B_combo` run met the precise brief's own rules (text 44px or more, an orange highlighted bar, labels and title exactly as asked; by eye in all six). The scripted `highlight_styling` flag reads false for `B_brief_r2` and `B_combo_r3` only because their CSS has no highlight keyword; the orange bar is there in both frames.
- Against the pre-registered guesses: H22 true (medians -65% and -73%, every run cheaper); H23 false (`B_brief` took 9, 10 and 14 turns, `B_combo` 9, 15 and 18; the baseline 25 to 34); H24 true (the highest peak was 71K).
- `B_combo` against `B_brief`: the median is 22% cheaper ($0.0076 vs $0.0097) from the smaller start context (7K vs 20K), but its turn counts overlap and are higher (15 and 18 vs 10 and 14), so with n=3 the combination is not clearly better than the precise brief alone.
- The baseline was the tightest cell (cost within 5% of its median); the precise-brief cells varied more, mostly through turn count.
- Limits: n=3 per cell; one task; Haiku 5.5 High; fixture and scorer unchanged.
