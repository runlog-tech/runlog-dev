# Antigravity CLI Context Protocol & Verification Methodology

**Document Version:** 1.0.0  
**Target Binary:** `agy` v1.2.13 (Google Antigravity CLI)  
**Evaluator:** RUNLOG Benchmark Lab  
**Artifact Classification:** Empirical Verification Protocol  

---

## 1. Executive Summary & Binary Ground Truth

During the review of Video 18, an audit requested the verbatim stdout dump of `agy /context` across Checkpoints 1 through 3 to verify prompt token accumulation.

When attempting to execute `/context` non-interactively via the CLI print runner:
```bash
agy --conversation=d2b06ff9-bf8d-4400-b4d6-48f155523ffe --print="/context"
```

The `agy` CLI binary exits with return code `2` and outputs the following verbatim error:
```text
error: /context is not available in print mode (it opens the interactive context breakdown); pass --disable-slash-commands to send /context to the model as literal text
```

### Technical Root Cause
In Google Antigravity (`agy`), slash commands (`/context`, `/help`, `/model`, `/clear`) are handled exclusively by the interactive Terminal User Interface (TUI) runtime. They are not CLI flags and cannot be rendered or piped in `--print` (headless) mode.

For automated pipelines, benchmarking, and machine-readable telemetry, `agy` provides the official `--output-format json` flag. This outputs a structured JSON envelope containing the exact, authoritative API usage metrics returned by the Gemini backend.

---

## 2. Programmatic Context Measurement Protocol

To capture verbatim token usage at each benchmark checkpoint without manual TUI screen-scraping, the test runners (`run_cp1.py`, `run_cp2.py`, `run_cp3_highwatermark.py`) invoke `agy` with:

```bash
agy \
  --dangerously-skip-permissions \
  --output-format json \
  --model gemini-3.8-flash-medium \
  --conversation=<CONVERSATION_ID> \
  --print="<PROMPT>"
```

### JSON Telemetry Schema
The stdout stream returns the following schema:
```json
{
  "conversation_id": "03662f32-0c08-42d4-8cf6-09e4c9d27339",
  "response": "...",
  "duration_seconds": 474.4,
  "usage": {
    "input_tokens": 617319,
    "output_tokens": 58866,
    "thinking_tokens": 10557,
    "cache_read_tokens": 1931439,
    "total_tokens": 676185
  }
}
```

The underlying metrics in `receipts/checkpoint_N_context.txt` were extracted directly from these real, verbatim JSON responses.

---

## 3. The 1,448,801 Token High-Watermark (Turn 40) — unresolved, not published

A CP-3/CP-4 run (continuing the CP-2 conversation to Turn 40) reported
`gauntlet_usage.input_tokens: 1,448,801`. Gemini 3.8 Flash's documented
context window is **1,048,576 tokens (1M)** — a single API request
can't legitimately exceed that.

### What we checked
One candidate explanation: a complex turn triggers multiple sub-actions
(file writes, directory scans, shell tests), and `agy`'s
`--output-format json` might aggregate cumulative input tokens across
**all API calls within that turn** rather than reporting one call's
actual context size — which would mean the raw number isn't what it
looks like.

**This explanation does not fully hold up.** `checkpoint_3_results.json`'s
own `turns[]` array — the same per-turn `usage` schema that CP-1 and
CP-2 use normally, growing consistently turn over turn without
inflation through Turn 24's real 617,319 — already shows **Turn 39 at
1,298,820 input tokens**, over the ceiling, in a single ordinary turn,
before the flagged aggregated gauntlet field is even reached. We do not
have a confirmed explanation for that.

### What this means for the published results
- We do **not** claim a 1.4M context window for Gemini 3.8 Flash.
- This repo's published receipts (`checkpoint_1_results.json`,
  `checkpoint_2_results.json`) stop at CP-2 / Turn 24, **617,319
  tokens**, which is internally consistent with every other
  checkpoint and safely under the documented window.
- At 617,319 tokens (~59% of the 1M window), Antigravity operates right
  at the threshold where Claude Code triggers automatic compaction
  (`autoCompactWindow: 700000`), which is why that's the number used
  for the video's apples-to-apples comparison.
- The CP-3/CP-4 run and its anomalous numbers are described, not
  included, in this repo — see `benchmark_plan.md` section 6C.

---

## 4. Verbatim Checkpoint Receipts

### Checkpoint 1 (Low Overlap · Turn 10)
- **Session:** `d2b06ff9-bf8d-4400-b4d6-48f155523ffe`
- **File:** `receipts/checkpoint_1_results.json` (Turn 10)
- **Input Tokens:** 196,315
- **Cache Read Tokens:** 1,020,963
- **Output Tokens:** 24,476
- **Total Tokens:** 220,791
- **Constraint Retention:** 12 / 12 (100%)

### Checkpoint 2 (Mid-Scaling / Auto-Compact Boundary · Turn 24)
- **Session:** `03662f32-0c08-42d4-8cf6-09e4c9d27339`
- **File:** `receipts/checkpoint_2_results.json` (Turn 24)
- **Input Tokens:** 617,319
- **Cache Read Tokens:** 1,931,439
- **Output Tokens:** 58,866
- **Total Tokens:** 676,185
- **Constraint Retention:** 12 / 12 (100%)

### Checkpoint 2 Gauntlet (Turn 25 Trigger)
- **Session:** `03662f32-0c08-42d4-8cf6-09e4c9d27339`
- **File:** `receipts/checkpoint_2_results.json` (`gauntlet_usage`)
- **Input Tokens:** 717,723
- **Cache Read Tokens:** 2,098,154
- **Output Tokens:** 66,663
- **Total Tokens:** 784,386
- **Constraint Retention:** 12 / 12 (100%)
