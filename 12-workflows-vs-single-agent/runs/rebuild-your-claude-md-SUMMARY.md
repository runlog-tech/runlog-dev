# rebuild-your-claude-md pair, 2026-10-04 (rep 2)
| | single | workflow |
|---|---|---|
| wall | 43s | 80s |
| cost (result.json total_cost_usd) | $0.2678 | $1.3744 (5.1x) |
| tokens, all four usage fields summed | 181,646 | 1,326,703 across 14 agent transcripts (7.3x) |
| claims extracted / checked | 14 / 8 | 23 / 8 |
| flagged | 5 items (C1 overstated, C3 framing, C6 wording, L38 missing exhibit, unreceipted C5/C7) | 4 contradicted (c1, c5, c7, c9), 4 passed |
| /usage session before -> after | 17% -> 17% (next run's before read 19%) | 19% -> 31% (+12) |
| /usage week | 68% -> 68% | 68% -> 69% |
Token basis: includes cache reads; earlier pairs used each agent's own usage report, so ratios are not strictly comparable.
