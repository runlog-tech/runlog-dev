# One oversized prompt: how agy and Claude Code handle it

Run 2026-10-03, agy 1.2.15 (gemini-3.8-flash-medium, `--mode plan`) and `claude -p --model haiku`, each given ONE message built by `protocol/run_big.py`.
The message: a vault code on the first line, filler paragraphs, a "paging threshold" sentence at the midpoint, and a final question asking for both values with no tools.
S = 830,217 bytes (about 140K prompt tokens for Claude, about 117K by agy's fitted 7.07 bytes/token; the early 5.5 bytes/token guess was too low). L = 2,200,305 bytes (roughly 2.7x larger, so well above both limits).

| Run | Result | Context per call | Vault code (start) | Paging value (middle) | Question (end) |
|---|---|---|---|---|---|
| agy S | accepted, 1 reply, 12 s | 39,264 | returned | not returned | never seen |
| agy L | accepted, 1 reply, 11 s | 39,230 | returned | not returned | never seen |
| Claude S | error `Prompt is too long`, 3 s | none | n/a | n/a | n/a |
| Claude L | error `Prompt is too long`, 4 s | none | n/a | n/a | n/a |

## What agy does

agy does not compact and does not error. It truncates the user message: it kept the first 192,000 characters (187,644 bytes of the prompt body in both runs), dropped the rest, and appended `<truncated 642573 bytes> NOTE: The output was truncated because it was too long...` (S) or `<truncated 2012661 bytes>` (L). The stored transcript is in `*/stored-user-input-head-and-marker.txt` (start and marker only).

Because the question sat at the end, the model never saw it. It replied "Noted. Vault code COBALT-... recorded." The vault code survived because it was at the head. The paging sentence sat in the dropped middle.

The per-call context stayed at about 39K, so one oversized message did not reach the ~130K compaction trigger. The enforced limit is a character cap (192,000 characters), not a token cap; the token count depends on the text (see the review below). Compaction only fires on accumulated context across calls (see `../README.md`).

Scoring note: `paging_ok` first read True for agy L because the substring "115" appears inside "COBALT-1159". Rescored with a word-boundary regex: False. The summary.json files say so.

## What Claude Code does

Both sizes are rejected before any model call with `Prompt is too long` (`is_error: true`, no usage). Nothing is truncated or compacted. S was rejected. The bisect below puts the limit between 680,937 and 697,500 bytes. The user's global CLAUDE.md (about 23K tokens) was also loaded.

## Limits of this test

- One run per cell, one model per tool, random-word filler.
- agy's tool-file path is different: reading a big file with the view tool is capped at 46,080 bytes per read (see `../README.md`). That cap and this 192,000-character cap on a typed message are separate limits.
- Only the head was kept in both agy runs; whether agy ever keeps the tail was not tested (the marker sat at character 192,001 in both).

## agy's own review (`agy-review.md`, prompt in `agy-review-prompt.txt`)

agy (read-only, `--mode plan`, no shell) checked claims C1 to C6 against copies of its own transcripts. It CONFIRMED C1 to C4 and C6 with file and field evidence, and said C5 overstated "a token cap": the limit is a character cap and the token total depends on the text.

Where its answers are weaker than they read (our assessment, not agy's):

- Q1 (why 192,000, not configurable): inferred from the marker wording ("output was truncated... smaller range") and from not finding a setting. No source or doc was cited. Treat as unverified.
- Q2 ("head always kept, tail never"): only two runs, both with the marker at character 192,001. It did not test a case where the tail is kept.
- Q3 (~12.7K base + 26.5K prompt = 39.2K, "within 0.08%"): circular. It fitted 7.07 bytes/token to the residual after assuming a 12.7K base. It does show our 5.5 bytes/token estimate is probably too low for agy: at 7.07, S is about 117K tokens, below the compaction trigger. S was still truncated, because the cap is characters.
- Q4 (put big documents in a file, up to 100 MB via view_file paging): the 46,080-byte per-read limit is quoted from its tool definition; the 100 MB figure and the advice were not tested here.

## Claude Code threshold (bisect, `claude-bisect/`, `protocol/bisect_claude.py`)

Same prompt builder, Haiku via `claude -p`, one run per size, sequential. Context per call = input + cache read + cache creation, and it includes about 23K tokens of the user's global CLAUDE.md.

| Prompt bytes | Result | Context per call |
|---|---|---|
| 300,000 | OK, both values returned | 73,459 |
| 565,000 | OK, both values returned | 118,257 |
| 631,250 | OK, both values returned | 129,466 |
| 664,375 | OK, both values returned | 135,066 |
| 680,937 | OK, both values returned | 137,892 |
| 697,500 | `Prompt is too long`, no model call | none |

The limit sits between 680,937 and 697,500 bytes, which is between 137,892 and roughly 141,000 tokens of context. That is well below a 200K window. This test did not find out why (a plan or model limit, or a client-side check). Do not call it a model context window.

Claude's tokenizer on this filler comes out near 6 bytes per token (about 6.0 to 6.2 after subtracting the ~23K baseline), not the 5.5 we estimated. So the 830 KB prompt is about 140K tokens of prompt for Claude, not 150K; agy's fitted figure for the same text was about 7.07 bytes per token, so token counts are not comparable across the two tools.

Everything below the limit was answered correctly, including the value in the middle of the prompt: Claude uses the whole prompt up to the limit and rejects above it, while agy cuts at 192,000 characters.
