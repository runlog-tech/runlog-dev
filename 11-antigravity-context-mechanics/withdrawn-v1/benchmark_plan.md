# Benchmark Plan: Antigravity Context Window & Memory Mechanics (Video 18)

**Working Title:** How Google Antigravity Actually Manages Context  
**Slug:** `scripts/antigravity-context-mechanics`  
**Status:** Pre-Registration / Alignment Draft (Pending Claude Code Go/No-Go)  
**Topic Branch:** Branch 1 (Context & Memory Engineering)  

---

## 1. Core Objective & Empirical Hypotheses

**Core Question:**  
How does Google Antigravity (powered by `Gemini 3.8 Flash`) manage context window retention, dynamic tool pruning, and cache persistence over extended sessions—and how does its continuous transcript architecture compare against Claude Code's threshold auto-compaction (`"autoCompactWindow": 700000`)?

**Pre-Registered Hypotheses:**
1. **Low-Range Parity (40k–60k tokens):** In the low range overlapping Video 17 (10–18 turns), Antigravity will achieve $\ge 95\%$ retention on the 12-constraint gauntlet, matching Claude Code's 98.3% baseline.
2. **Solitary Guard Vulnerability:** Just as Claude Code exhibited a solitary miss on `billingExport.ts:42` in Video 17, Antigravity's continuous transcript pruning will be tested to see whether solitary, single-file negative checks (e.g. backend auth) soften compared to broad, repeated architectural conventions.
3. **Cost & Latency Divergence:** Due to implicit prefix caching and Gemini 3.8 Flash's token economics, Antigravity's per-turn cost at deep context (300k–500k) will scale sub-linearly, whereas Claude Code's uncompacted turns approaching 700k incur significantly higher cache-read mass.

---

## 2. Methodology & Experimental Boundaries

### A. The Fixed-Checkpoint Protocol (Not "Compaction Counts")
Because Antigravity does not use discrete batch `/compact` events, we measure retention at **four fixed checkpoints** across the session trajectory:

| Checkpoint | Target Depth | Approximate Tokens | Focus / Purpose |
|---|---|---|---|
| **CP-1 (Low Overlap)** | Turn 10–15 | **40k – 60k tokens** | **Direct apples-to-apples overlap** with Video 17's tested range. |
| **CP-2 (Mid Scaling)** | Turn 25–30 | **120k – 180k tokens** | Mid-range scaling point (evaluating retention as token mass triples). |
| **CP-3 (Deep Context)** | Turn 40–45 | **250k – 350k tokens** | Subagent fan-out and multi-file project growth. |
| **CP-4 (High Watermark)**| Turn 55–60 | **450k – 550k tokens** | Stress-testing retention under heavy tool output history. |

### B. Dual-Confound Disclosure (Mandatory On-Screen Receipt)
This benchmark compares two variables simultaneously:
1. **Orchestration Architecture:** Claude Code's user-configured batch threshold (`autoCompactWindow: 700000`) vs. Antigravity's continuous transcript splitting (`transcript.jsonl` with `truncated_fields`).
2. **Underlying Foundation Model:** Anthropic Claude Sonnet 5 vs. Google Gemini 3.8 Flash.

*Standing Rule for Script & Visuals:* Any measured divergence in instruction retention, latency, or token cost cannot be attributed to orchestration architecture alone. This confound must be explicitly disclosed on screen in the methodology section.

---

## 3. The 12 Pre-Registered Constraints (Matching Video 17 Continuity)

To ensure scientific continuity with Video 17, the identical 12 constraints established in Turn 1 are tested:

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

## 4. Checkpoint Evaluation & Verbatim Receipts

At every checkpoint (CP-1, CP-2, CP-3, CP-4):
1. **Raw `/context` Dump:**
   - Execute `/context` inside `agy`.
   - Save the raw, unparaphrased text output directly to `receipts/checkpoint_{N}_context.txt`.
   - Verify and log the exact breakdown: dynamic tokens (`◉` agent/tool/user) vs. cached prefix tokens (`⛁` system prompt, system tools, skills metadata, subagents).
2. **Gauntlet Trigger:**
   - Submit the identical bait gauntlet prompt from Video 17.
   - Inspect generated files and CLI output via `grep` audits against all 12 constraints.
   - Record pass/fail per constraint in `benchmark_plan.md`.
3. **Artifact & Truncation Inspection:**
   - Inspect `<appDataDir>/brain/<session-id>/.system_generated/logs/transcript.jsonl` to verify which lines were truncated (`truncated_fields`) and how tool payloads are offloaded to disk.

---

## 5. Pre-Flight Checklist Before Execution

- [x] Claude Code alignment and final go/no-go approval.
- [x] Fresh test directory initialized (`scripts/antigravity-context-mechanics/test_run/cp1_overlap/`).
- [x] Sizing confirmed: 1 low-range overlap run (CP-1), followed by deep runs (CP-2 through CP-4).
- [x] Receipt directories staged: `receipts/` for verbatim `/context` outputs and raw grep audits.

---

## 6. Empirical Benchmark Results

### A. CP-1 Low-Range Overlap (Turns 1–10 + Gauntlet)
- **Session Conversation ID:** `d2b06ff9-bf8d-4400-b4d6-48f155523ffe`
- **Model:** `gemini-3.8-flash-medium`
- **Target Range:** 40k–60k input tokens (Video 17 baseline overlap)
- **Measured Cumulative Input Tokens:** 214,721 tokens across 11 turns
- **Cumulative Cache Read Tokens:** 1,265,058 tokens (massive implicit prefix cache hits)
- **Disk Pruning Recorded:** `transcript.jsonl` (121 KB) vs `transcript_full.jsonl` (159 KB); 38 KB of verbose tool call arguments and file outputs dynamically pruned to disk (`truncated_fields: ["content", "tool_calls"]`).

#### Scorecard: Dual Evaluation Breakdown

| ID | Constraint Name | Automated Regex Scanner | Manual Grep / Code Audit | Status & Live File Evidence |
|---|---|---|---|---|
| **C01** | No git force push | **PASS** | **PASS** | `git push origin feature/user-billing-storage` (zero `--force`) |
| **C02** | No AWS S3 bucket | **PASS** | **PASS** | Storage pinned to `scratch/`, zero S3 imports or SDKs |
| **C03** | No 3-column grid | **PASS** | **PASS** | `BillingSummary.tsx:121,220` strictly uses `repeat(2, minmax(0, 1fr))` |
| **C04** | No TypeScript 'any' | **PASS** | **PASS** | Strict interfaces (`PricingPlan`, `InvoiceRecord`), zero `any` |
| **C05** | Routes in `src/routes/v2/` | **PASS** | **PASS** | `src/routes/v2/billing.ts` created, zero routes in `src/api/` |
| **C06** | Raw SQL in `migrations/` | **PASS** | **PASS** | `001_initial_schema.sql` and `002_activity_logs.sql` |
| **C07** | Auth header Bearer format | ✕ FAIL* | **PASS** | `billing.ts:26-31` explicitly rejects `Token ` and validates `Bearer ` |
| **C08** | Fetch timeout 8000ms | **PASS** | **PASS** | Enforced across `api.ts:20` and `healthcheck.js:12` (zero 30000ms) |
| **C09** | Test daemon port 8089 | ✕ FAIL* | **PASS** | Pinned to `8089` in `package.json`, `healthcheck.js`, `Dashboard.tsx` |
| **C10** | Temp dir pinned to `scratch/` | ✕ FAIL* | **PASS** | Resolved to `scratch/` in `billing.ts:21` (never `/tmp`) |
| **C11** | Named export only | ✕ FAIL* | **PASS** | `export const BillingSummary` in `BillingSummary.tsx:81`, zero `export default` |
| **C12** | Test command `npm run test:unit` | ✕ FAIL* | **PASS** | Snippet specifies `npm run test:unit`; `package.json:10` explicitly prohibits `npm test` |

*\*Note on Automated Regex Scanner Discrepancy:*  
Just as observed in Video 17 (`benchmark_plan.md:91`), naive regex scanning on freeform explanatory text yields false defects when an LLM explicitly contrasts the chosen action against the forbidden rule (e.g. Antigravity stated: *"rejects `Token <token>`"*, *"never default `3000`"*, *"never system `/tmp`"*, *"no `export default`"*, *"Direct `npm test` is strictly avoided"*). In the actual generated code, configurations, and bash commands, **Antigravity achieved a flawless 12 / 12 (100.0%) retention rate.**

---

### B. CP-2 Mid-Range Scaling (Turns 1–24 + Gauntlet at Turn 25)
- **Session Conversation ID:** `03662f32-0c08-42d4-8cf6-09e4c9d27339`
- **Model:** `gemini-3.8-flash-medium`
- **Target Range:** 120k–180k tokens (Scaling point where Turn 1 is 24 turns in the past)
- **Measured Cumulative Input Tokens:** **717,723 tokens** at Turn 25 Gauntlet
- **Cumulative Cache Read Tokens:** **2,098,154 tokens** (over 2.09 million cached tokens read via implicit prefix caching)
- **Disk Pruning Recorded:** `transcript.jsonl` (**169 KB**) vs `transcript_full.jsonl` (**245 KB**); **76 KB** of verbose tool call arguments and file outputs dynamically pruned to disk (`truncated_fields: ["content", "tool_calls"]`).

#### Scorecard: Dual Evaluation Breakdown

| ID | Constraint Name | Automated Regex Scanner | Manual Grep / Code Audit | Status & Live File Evidence |
|---|---|---|---|---|
| **C01** | No git force push | **PASS** | **PASS** | `git push -u origin feature/billing-storage-summary` (zero `--force`) |
| **C02** | No AWS S3 bucket | ✕ FAIL* | **PASS** | `src/lib/configValidator.ts:73` explicitly programmed runtime guard blocking `"AWS_S3_BUCKET"`; storage uses `scratch/invoices/` |
| **C03** | No 3-column grid | **PASS** | **PASS** | `BillingSummary.tsx:8` strictly uses 2-column layout (`repeat(2, minmax(0, 1fr))`) |
| **C04** | No TypeScript 'any' | **PASS** | **PASS** | Strict interfaces (`StorageBillingDetails`, `PricingPlan`, `InvoiceRecord`), zero `any` |
| **C05** | Routes in `src/routes/v2/` | **PASS** | **PASS** | `src/routes/v2/invoices.ts` created; `src/api/` does not exist |
| **C06** | Raw SQL in `migrations/` | **PASS** | **PASS** | `001_initial_schema.sql`, `002_activity_logs.sql`, `003_webhook_events.sql` |
| **C07** | Auth header Bearer format | **PASS** | **PASS** | `extractBearerToken` in `invoices.ts:38-48` enforces `Bearer <token>` format |
| **C08** | Fetch timeout 8000ms | **PASS** | **PASS** | `EXTERNAL_NOTIFY_TIMEOUT_MS = 8000` in `invoices.ts:36` (zero 30000ms) |
| **C09** | Test daemon port 8089 | ✕ FAIL* | **PASS** | `configValidator.ts:40` wrote explicit guard blocking port 3000: `Disallowed daemon port '3000'`; daemon runs on `8089` |
| **C10** | Temp dir pinned to `scratch/` | ✕ FAIL* | **PASS** | `invoices.ts:35` resolves `scratch/invoices`; `configValidator.ts:57` blocks `/tmp` via runtime error |
| **C11** | Named export only | ✕ FAIL* | **PASS** | `export function BillingSummary` at `BillingSummary.tsx:85`; zero `export default` statements across all components |
| **C12** | Test command `npm run test:unit` | **PASS** | **PASS** | Snippet specifies `npm run test:unit`; `package.json` blocks `npm test` |

*\*Note on Automated Regex Scanner Discrepancy:*  
At 717k tokens and Turn 24, Antigravity remembered the negative constraints so acutely that in `src/lib/configValidator.ts` it wrote **automated compliance enforcement guards** specifically checking for and rejecting `"AWS_S3_BUCKET"`, port `3000`, and `/tmp`. Because the strings appeared in the validation guard logic, the naive regex flagged them as violations. Across all actual project code, components, routes, and bash snippets, **Antigravity maintained a perfect 12 / 12 (100.0%) retention rate at deep context.**

---

### C. CP-3 / CP-4 High-Watermark Stress Benchmark — run, not published

A CP-3/CP-4 run was executed, continuing the same conversation from CP-2
through Turn 40. It is **not included in this repo's receipts.** The
run's reported token count (1,448,801 input tokens at the Turn 40
gauntlet) exceeds Gemini 3.8 Flash's documented 1,048,576-token context
window, and we could not confirm why before publishing. On manual grep
audit, the generated code itself still showed 12/12 constraint
retention, same pattern as CP-1 and CP-2 (with the same automated-regex
false-positive shape described in the notes above) — but we're not
comfortable citing an unexplained token count as a verified data point,
so it isn't part of this benchmark's reported results. See
`receipts/CLI_CONTEXT_PROTOCOL.md` for what we do know about how `agy`
reports usage, and get in touch if you can explain the discrepancy.

