# Results (hand-audited)

Y = correct from memory, no tool use. Y* = correct but only after re-reading with tools. N = wrong or "not in memory".

| Run | M1 | M2 | M3 | M4 | M4B | M5 | M6 |
|---|---|---|---|---|---|---|---|
| agy rep 1 | Y | Y | Y | Y | Y | Y | Y |
| agy rep 2 | Y | Y | Y | Y | Y | Y | Y* (3 tool calls) |
| agy rep 3 | Y | Y | Y | Y | Y | Y | Y |
| claude rep 1 | Y | Y | Y | Y | Y | Y | N |
| claude rep 2 | Y | Y | Y (hedged) | Y | Y | Y | N |
| claude rep 3 | Y | Y (no clean baseline, see audit) | Y | Y | Y | Y | N |
| agy control 1 | Y | Y | Y | Y | Y | Y | n/a (never read) |
| claude control 1 | Y | Y | Y | Y | Y | Y | n/a (never read) |

Audit notes:

- claude rep 3 M2: `sum.ts` written after compaction has the header, but the three feature files written before compaction do not (baseline `hdr: false` in `state.json`). Post-compaction pass, no clean baseline.
- agy rep 2 M6: probe forbade tools; agy made 3 `view_file` calls anyway. Reported separately from "from memory".
- Controls do not read the spec file holding M6, so M6 is untested there.
- agy version during the runs: 1.2.15.
- claude rep 2 M3: the answer names GRANITE-2804 (correct) and then says the summary lacks the details. Counted as survived with a hedge.
- claude rep 1 to 3 M6: "I don't have that information in memory."
- M5 order verified by de-duplicating file names in the answer (agy prints each file twice, as link text and path).

## Context and compaction

| Run | Peak context per call | Compaction |
|---|---|---|
| agy rep 1 | 133,550 | 131,236 to 14,523 (between two consecutive calls) |
| agy rep 2 | 135,279 | 132,202 to 14,409 (between two consecutive calls) |
| agy rep 3 | 135,368 | 130,088 to 14,504 (between two consecutive calls) |
| claude rep 1 | 137,736 | /compact pre 137,800, post 3,930 |
| claude rep 2 | 136,028 | /compact pre 136,304, post 3,946 |
| claude rep 3 | 134,483 | /compact pre 134,563, post 4,077 |
| agy control 1 | 24,999 | none |
| claude control 1 | 27,377 | none |

Context per agy call = input_tokens + cache_read_tokens. Context per Claude call = input + cache_read + cache_creation, with assistant events de-duplicated by message id.

## Does the compaction summary contain the buried sentence?

| Run | Summary has M6 |
|---|---|
| agy rep 1 | yes |
| agy rep 2 | no (agent re-read the file) |
| agy rep 3 | yes |
| claude rep 1 | no |
| claude rep 2 | no |
| claude rep 3 | no |
