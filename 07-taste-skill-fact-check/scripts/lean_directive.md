# The lean directive (Arm E)

The 4-line, 129-token alternative benchmarked against `taste-skill`'s
21,998-token v2 `SKILL.md`. This is the entire system prompt for Arm E —
no other instructions were given to the model.

```
DESIGN CONSTRAINTS:
1. Palette: Dark zinc-950/charcoal (#09090b ground, #18181b cards), single cyan or amber accent. NO purple gradients.
2. Layout: Asymmetric 2-column or staggered layout. Strictly NEVER use a generic 3-column equal feature card row.
3. Copy & Typography: Concrete technical terminology only. Ban startup buzzwords (seamless, elevate, next-gen). Typography hierarchy via font weight, not oversized screamers.
4. Clean Code: Real SVG icons or clean semantic primitives, no div-based fake terminal mocks.
```

Real result, graded against taste-skill's own 50-item ban list: 0/3 clean
across the 3 test briefs — same as the naked baseline (0/3), while
`taste-skill` v2 itself landed at 5/8 clean (1 of 9 generations excluded
as a documented truncation gap). See the video for the full breakdown:
the lean directive isn't a hidden winner, it's a cheap first pass that
still lets through the same violations (a 3-column grid slipped through
in every arm type tested, including this one).
