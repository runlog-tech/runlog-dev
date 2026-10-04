### Verification of Claims C1–C6

| Claim | Status | Exact Evidence (File, Field, Number) |
|---|---|---|
| **C1** | **CONFIRMED** | • [truth.json](file:///home/invii/retest-work/handoff2/receipts/big-agy-S/truth.json#L1): `bytes: 830217`<br>• [truth.json](file:///home/invii/retest-work/handoff2/receipts/big-agy-L/truth.json#L1): `bytes: 2200305`<br>• [out.ndjson](file:///home/invii/retest-work/handoff2/receipts/big-agy-S/out.ndjson#L6) & [out.ndjson](file:///home/invii/retest-work/handoff2/receipts/big-agy-L/out.ndjson#L6): `status: "SUCCESS"`, `exit: 0`, `is_error: null`<br>• [transcript_full.jsonl (S)](file:///home/invii/retest-work/handoff2/agy-logs/S/transcript_full.jsonl#L1) & [transcript_full.jsonl (L)](file:///home/invii/retest-work/handoff2/agy-logs/L/transcript_full.jsonl#L1): `step_index: 0, status: "DONE"` without error. |
| **C2** | **CONFIRMED** | • [transcript_full.jsonl (S)](file:///home/invii/retest-work/handoff2/agy-logs/S/transcript_full.jsonl#L1): marker `<truncated 642573 bytes>\n\nNOTE: The output was truncated because it was too long...`<br>• [transcript_full.jsonl (L)](file:///home/invii/retest-work/handoff2/agy-logs/L/transcript_full.jsonl#L1): marker `<truncated 2012661 bytes>\n\nNOTE: The output was truncated because it was too long...`<br>• Prompt body kept: `830,217 - 642,573 = 187,644` bytes (S) and `2,200,305 - 2,012,661 = 187,644` bytes (L); marker placed at character 192,001. |
| **C3** | **CONFIRMED** | • [run_big.py](file:///home/invii/retest-work/handoff2/run_big.py#L25-L33): question was appended at the very end of the prompt (after target byte count), which fell in the truncated tail (>187.6 KB).<br>• [transcript_full.jsonl (S)](file:///home/invii/retest-work/handoff2/agy-logs/S/transcript_full.jsonl#L2): response is `"Noted. Vault code `COBALT-3158` has been recorded."`; model `thinking` confirms it only parsed the vault code and filtered the remaining stream as noise.<br>• [transcript_full.jsonl (L)](file:///home/invii/retest-work/handoff2/agy-logs/L/transcript_full.jsonl#L2): response is `"Noted. Vault code `COBALT-1159` is recorded. How can I assist you with your project?"` |
| **C4** | **CONFIRMED** | • [out.ndjson (S)](file:///home/invii/retest-work/handoff2/receipts/big-agy-S/out.ndjson#L5): `input_tokens: 39264`, `cache_read_tokens: 0`.<br>• [out.ndjson (L)](file:///home/invii/retest-work/handoff2/receipts/big-agy-L/out.ndjson#L5): `input_tokens: 39230`, `cache_read_tokens: 0`.<br>• [summary.json (S & L)](file:///home/invii/retest-work/handoff2/receipts/big-agy-S/summary.json#L8): `events: []` (no compaction boundary fired). |
| **C5** | **CONFIRMED** (with nuance) | • [claims.md](file:///home/invii/retest-work/handoff2/claims.md#L7): Because individual user messages are clamped at 192,000 characters (~26.5K tokens) and base prompt context is ~12.7K tokens, a single turn can only ever reach ~39K tokens context.<br>• Consequently, context can never reach the ~130K compaction threshold in a single user turn; compaction requires multiple turns/calls. |
| **C6** | **CONFIRMED** | • System prompt tool definition for `view_file`: `"Content is limited to 46080 bytes per view. If content is truncated, use the ContentOffset parameter to view the remaining content."`<br>• The user input message cap is 192,000 characters (~187.6 KB retained), which is more than 4× larger than and independent of the 46,080-byte `view_file` per-read limit. |

---

### Overstated Claims

- **C5 in [claims.md](file:///home/invii/retest-work/handoff2/claims.md#L7)**: Stating that a single message is *"capped near 39K tokens per call"* overstates tokens as the enforcing metric. The actual constraint is a **character/byte cap** (192,000 characters / 187,644 prompt body bytes). The ~39K token count is an artifact of ~12.7K base tokens plus the token density of English filler words (~7.1 bytes/token). Denser or sparser text would produce different token counts under the same 192,000 character limit.

---

### Questions Q1–Q4

#### Q1. Source of the 192,000-character cap & configurability
* **Answer**: It is a generic string-truncation guardrail reused across the pipeline for user input. The marker text itself—`"NOTE: The output was truncated because it was too long. Use a more targeted query or a smaller range to get the information you need."`—uses output/query/range terminology originally written for tool, command, and query outputs. It is a hardcoded CLI harness ceiling and is **not configurable** via CLI flags or user settings.
* **Basis**: Direct evidence from transcript marker text in [transcript_full.jsonl](file:///home/invii/retest-work/handoff2/agy-logs/S/transcript_full.jsonl#L1) (reused output wording); belief about design regarding hardcoded non-configurability.

#### Q2. Truncation direction (head vs. tail) & meaning to the model
* **Answer**: The head is always kept (`text[:limit]`) and the tail is dropped; there is no provision to retain the tail of an oversized user input. To the model, the truncation marker looks like raw message content. In both runs, the model's internal thinking treated the truncated stream as noisy/obfuscated data accompanying the opening access note, acknowledged the surviving vault code at the top, and ignored the rest because the question at the bottom never existed in its context.
* **Basis**: Direct evidence from [transcript_full.jsonl](file:///home/invii/retest-work/handoff2/agy-logs/S/transcript_full.jsonl#L1-L2) (`thinking` field and character positioning).

#### Q3. Composition of ~39K context & arithmetic check
* **Answer**:
  - **Base context (~12.7K tokens)**: System prompt instructions, mode prompt (`--mode plan`), and complete JSON schemas for 60 declared tools (listed in [out.ndjson](file:///home/invii/retest-work/handoff2/receipts/big-agy-S/out.ndjson#L1)).
  - **Kept user prompt (~26.5K tokens)**: 187,644 bytes of ASCII words separated by spaces tokenize at ~7.07–7.08 bytes/token in Gemini (`187,644 / 7.07 ≈ 26,540 tokens`).
  - **Total**: `12,700 + 26,540 = 39,240 tokens`, matching `input_tokens` of 39,264 (run S) and 39,230 (run L) within ~0.08%.
* **Basis**: Direct evidence from tool definitions in [out.ndjson](file:///home/invii/retest-work/handoff2/receipts/big-agy-S/out.ndjson#L1) and usage metrics in [out.ndjson](file:///home/invii/retest-work/handoff2/receipts/big-agy-S/out.ndjson#L5).

#### Q4. Best practice for ingesting very large documents
* **Answer**: Never paste very large text directly into the prompt message, as text past 192,000 characters is dropped with no retry mechanism. Instead, store the document in a file in the workspace and let the agent inspect it using [`view_file`](file:///home/invii/gemini), which accommodates files up to 100 MB via chunked paging (`ContentOffset`, `StartLine`, `EndLine` up to 46,080 bytes per call), or search it selectively with `grep_search` and delegate sections to subagents.
* **Basis**: Direct evidence from system tool specifications for `view_file` and observed prompt truncation behavior.
