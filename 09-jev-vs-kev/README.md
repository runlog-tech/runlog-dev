# jev-vs-kev

The real hook harness from RUNLOG's benchmark of Jev (TypeSafe AI's
cloud "System 1" decision model) and Kev (Jared Palmer's open-weights
local version), wired into both Claude Code and Antigravity as a
`PreToolUse` safety hook.

The pitch behind both models: a small, fast classifier can judge
whether a shell command is safe instead of asking a frontier model,
and Claude Code and Antigravity handle a flagged command completely
differently once one blocks it. Claude Code's hook contract can only
allow or hard-stop (POSIX exit code 0/2). Antigravity's hook contract
is richer: `allow` / `deny` / `ask` / `overwrite`, where `overwrite`
lets the hook silently substitute a safe command in place and keep
executing, no error, no extra turn.

## What's here

- `harness/kev_decision_engine.py` — calls a real local Kev-4B endpoint
  (Lemonade server, OpenAI-compatible completions API) and returns a
  verdict + a sanitized replacement command for destructive input.
- `harness/claude_hook.py` + `harness/claude_settings.json` — the real
  Claude Code `PreToolUse` hook: reads the tool call on stdin, exits 2
  on a destructive verdict, logs every call to `benchmark_data/`.
- `harness/antigravity_hook.py` — the real Antigravity `PreToolUse`
  hook: same decision engine, but returns the documented `overwrite`
  field instead of a hard block.
- `harness/run_live_harness_comparison.py` — drives both hooks against
  a shared set of test commands and records what each harness actually
  did (not simulated numbers).
- `benchmark_data/` — the raw logs these scripts actually produced.

## A note on `harness/run_benchmark.py`

This file is included for transparency, not as something to trust.
It was the source of this video's original headline claim (Claude
Code "burns 22,325 tokens and 7.67s per blocked hook"). Read
`evaluate_claude_code_harness()`: it returns a hardcoded
`tokens_burned: 2140` / `recovery_time_sec: 9.8` regardless of input,
with a docstring admitting it's an estimate ("Sonnet 3.5 burns
~1,900 tokens + ~9.5s"), not a measurement. It was never run against
a real Claude Code session.

The real number, measured by actually running `claude -p` against the
hook in `claude_hook.py` and reading `--output-format json` usage: a
blocked command costs about 150 output tokens and a one-line reply,
with no separable added latency beyond a normal turn.

Kev's ~191ms decision latency and Antigravity's `overwrite` mechanism,
by contrast, are real — reproduced live against the actual endpoint
and confirmed against Antigravity's own documented hook contract. Not
everything in this benchmark's original numbers was wrong, only the
Claude Code recovery-cost figures were invented.

## Reproducing it yourself

1. Run a local Kev endpoint (Lemonade server or equivalent OpenAI-compatible
   completions API) and point `kev_decision_engine.py`'s `LEMONADE_API_URL`
   at it.
2. Point `claude_settings.json`'s hook `command` at your local copy of
   `claude_hook.py`, then run `claude -p "..." --output-format json`
   against a command the hook will flag.
3. Read the real `usage` field in the JSON output instead of trusting
   a summary number, including someone else's.

`claude_settings.json` sets `"defaultMode": "bypass"` for
non-interactive benchmark runs only — don't carry that into a normal
working session.
