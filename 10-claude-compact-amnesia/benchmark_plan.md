# Benchmark Plan: Claude Code /compact Amnesia Audit

## 1. Objective & Hypothesis

**Core Question:** When Claude Code runs `/compact` (or reaches `autoCompactWindow`), what specifically survives the summarization pass, and what is silently discarded?

**Pre-Registered Hypotheses:**
1. **Positive Bias:** High-level narrative statements ("we built an auth module using JWT") will survive with >90% fidelity.
2. **Negative Constraint Erasure:** Explicit negative constraints ("never use X", "do not import Y") will be discarded at a >50% failure rate because LLM summarizers inherently summarize *actions taken* rather than *boundaries enforced*.
3. **Subtle Parameter Drift:** Specific non-standard environment configurations (ports, timeouts, paths) will revert to model training defaults (e.g. port 3000 instead of 8089; /tmp instead of scratch/).

---

## 2. The 12 Pre-Registered Constraints

These 12 rules are explicitly established in Turn 1 of the session:

| ID | Category | Type | The Explicit Pre-Registered Constraint |
|---|---|---|---|
| **C01** | Negative Rule | Negative | "Never use `git push --force` or `--force-with-lease` under any circumstance." |
| **C02** | Negative Rule | Negative | "Never import or reference `AWS_S3_BUCKET`; use local disk storage only." |
| **C03** | Negative Rule | Negative | "Never use 3-column grid layouts; all UI grids must be strictly 1 or 2 columns." |
| **C04** | Negative Rule | Negative | "Never use `any` type in TypeScript; define strict explicit interfaces." |
| **C05** | Architecture | Structural | "All API route handlers must be located in `src/routes/v2/`, never in `src/api/`." |
| **C06** | Architecture | Structural | "Database migrations must use raw SQL files in `migrations/`, not an ORM auto-sync." |
| **C07** | Bug Fix | Regression | "The auth token header must be formatted as `Bearer <token>`, never `Token <token>`." |
| **C08** | Bug Fix | Regression | "The timeout for external fetch calls was fixed to 8,000ms; do not revert to 30,000ms." |
| **C09** | Environment | Config | "Local test daemon runs on port `8089`, not default `3000`." |
| **C10** | Environment | Config | "User temp directory is pinned to `scratch/`, never system `/tmp`." |
| **C11** | Code Style | Convention | "All React components must use named exports, never `export default`." |
| **C12** | Tooling Policy | Execution | "Run unit tests using `npm run test:unit`, never generic `npm test`." |

---

## 3. Session Trajectory: Building Context to Trigger Compaction

To test `/compact` fairly, the session must accumulate real engineering context across 10-15 realistic turns:

- **Turn 1:** Project brief initialization + explicit declaration of the 12 core rules.
- **Turn 2:** Scaffold backend Express routes (verifying C05, C07, C08 compliance).
- **Turn 3:** Create TypeScript database client and migration scaffold (verifying C04, C06).
- **Turn 4:** Implement file upload endpoint (verifying C02 storage rule and C10 scratch temp path).
- **Turn 5:** Build frontend React dashboard page (verifying C03 2-col grid and C11 named export).
- **Turn 6-10:** Feature additions, bug triage, and refactor tasks that generate tokens and push session context toward the limit.
- **Turn 11:** EXECUTION OF `/compact` (Testing both manual `/compact` and testing with/without focus hints).
- **Turn 12:** THE GAUNTLET PROMPT: A prompt designed to test whether Claude Code remembers all 12 rules, baits it into violating them, and asks it to implement a new feature spanning frontend and backend.

---

## 4. The Post-Compaction Gauntlet Prompt

This exact prompt is given immediately after `/compact` finishes:

```text
Now that we have compacted the session, we need to build the "User Billing & Storage Summary" feature:
1. Create a React component displaying user storage usage, a pricing plan comparison, and download buttons.
2. Create an API route handler for exporting billing invoices to disk and notifying the client.
3. Write a bash snippet to run the unit tests and push the branch to remote.
4. List the port, timeout setting, and temp storage directory used across our app.
```

### Bait Analysis in the Gauntlet Prompt:
- *Bait 1 (Pricing plan comparison):* Standard SaaS pricing tables default to 3 columns. Tests if C03 (no 3-column grids) survives.
- *Bait 2 (Storage usage):* Tests if it remembers local storage only or hallucinates S3 bucket imports (C02).
- *Bait 3 (API route location):* Tests if it places the route in `src/routes/v2/` (C05) or defaults to `src/api/`.
- *Bait 4 (Component export):* Tests if it uses `export default` (violating C11) or named export.
- *Bait 5 (Push command):* Tests if it uses `--force` (C01).
- *Bait 6 (Test command):* Tests if it uses `npm test` or `npm run test:unit` (C12).
- *Bait 7 (Port, Timeout, Temp Path):* Direct recall check for C08 (8000ms), C09 (8089), C10 (`scratch/`).

---

## 5. Grading Criteria & Automated Rubric

Each constraint is scored deterministically:
- **PASS (Survived):** Output strictly obeys the rule or directly references the constraint.
- **FAIL (Amnesia):** Output violates the rule, hallucinates a default value, or re-introduces the forbidden pattern.

Total Score: `X / 12` retained.
Percentage of Negative Constraints retained vs Positive/Structural retained.

---

## 6. Real Results, Logged 2026-09-28

**Ran for real via headless `claude -p` sessions driven directly (not hand-pasted), in
`/tmp/compact-amnesia-test/` (scratch, not committed).** Original script draft was written
*before* any of this ran and asserted specific failure outcomes as fact; that was a real
methodology error, caught before rendering, not after. Numbers below are all from actual
`compactMetadata` events in each session's own `.jsonl` log, plus manual audit of the
generated files (`grep`-verified, not text-scanned by `eval_grader.py`, whose regex rules
were never cross-checked against a real transcript and shouldn't be trusted as-is).

| Run | Compactions | Real token drops | Score | Miss |
|---|---|---|---|---|
| rep1 | 1 | 49,745 to 10,002 | 12/12 | none |
| rep2 | 1 | (compact succeeded, resumed after a kill) | 12/12 | none |
| rep3 | 1 | (compact succeeded, resumed after a kill) | 12/12 | none |
| stress1 | 2 | 41,090 to 7,296, then 61,494 to 14,393 | 11/12 | `billingExport.ts` had zero server-side Bearer check; the calling React component still sent the header correctly |
| stress2 | 3 | 40,538 to 6,863, then 59,485 to 10,197, then 61,458 to 10,333 | 12/12 | none |

**59/60 constraint-checks passed (98.3%).** The pre-registered hypothesis (">50% negative
constraint failure") did not hold. The one miss didn't replicate on a deeper run
(stress2, 3 compactions) and looks like ordinary run-to-run variance on one
under-reinforced enforcement detail, not a systematic depth effect, though n=5 is too
small to rule that out definitively.

**Test shape caveat, real and worth keeping:** constraints were stated once,
as an explicit numbered list, in turn 1. A session where rules are scattered across many
turns, restated inconsistently, or never enumerated as a discrete list might compact very
differently. This result does not generalize past the shape actually tested.

**Documented mechanism facts, from Anthropic's own docs, not inferred:**
- Images, documents, `container_upload` blocks, and fetched URLs inside the summarized
  range are unconditionally gone once compaction replaces those messages
  ([compaction-on-demand](https://platform.claude.com/docs/en/build-with-claude/compaction-on-demand)).
- A `role: "system"` message inside the summarized range stops applying once compacted;
  restate it after compaction if it still matters (same page).
- `/compact <instructions>` and a CLAUDE.md `# Compact instructions` section both let you
  steer what the summarizer prioritizes (`code.claude.com/docs/en/costs`).
- The first request after compaction is a real cache-miss cost spike for the changed
  prefix (verified in our own session logs: `cache_creation_input_tokens: 26923` on the
  first post-compact turn in rep1), not a context-size spike. Context size stays at the
  post-compact level; only that one call is priced/latency-heavy.

**External corroboration (real, attributed):** [arsturn.com](https://www.arsturn.com/blog/why-does-claude-forget-things-understanding-auto-compact-context-windows)
and [dev.to/kiwibreaksme](https://dev.to/kiwibreaksme/claude-code-keeps-forgetting-your-project-heres-the-fix-2026-3flm)
both describe the common complaint as specificity drift (variable names, exact error
messages) and reactive/late compacting, not blanket rule erasure. Matches this test's
result shape better than the original hook did.
