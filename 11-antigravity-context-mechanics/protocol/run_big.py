#!/usr/bin/env python3
"""Single oversized prompt test. Usage: run_big.py <agy|claude> <S|L>. S ~150K tokens, L ~400K tokens, sent on stdin."""
import json, random, re, subprocess, sys, time
from pathlib import Path
import protocol as P

TOOL, SIZE = sys.argv[1], sys.argv[2]
TARGET_BYTES = int(SIZE) if SIZE.isdigit() else {"S": 830_000, "L": 2_200_000}[SIZE]
NAME = f"big-{TOOL}-{SIZE}"
WS = Path("/home/invii/retest-work/big") / NAME
OUT = Path(__file__).parent / "receipts" / NAME
WS.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
(WS / ("AGENTS.md" if TOOL == "agy" else "CLAUDE.md")).write_text("Keep answers short.\n")

rng = random.Random(4242 + (SIZE == "L"))
vault = f"{rng.choice(['EMBER','QUARTZ','SPRUCE','COBALT'])}-{rng.randint(1000, 9999)}"
paging = rng.randint(100, 999)
words = P.WORDS.split() if isinstance(P.WORDS, str) else list(P.WORDS)

def para():
    return " ".join(rng.choice(words) for _ in range(rng.randint(30, 60))).capitalize() + "."

head = f"ACCESS NOTE. VAULT CODE: {vault}. Remember it.\n\n"
mid_note = f"Operational note: the paging threshold is {paging} alerts per minute.\n\n"
tail = ("\n\nQUESTION. Reply with only two values on one line: the VAULT CODE stated at the very start of this message, "
        "and the paging threshold from the Operational note in the middle. Do not use any tools or open any file.")
body, size, mid_done = [], len(head), False
while size < TARGET_BYTES:
    p = para() + "\n\n"
    if not mid_done and size > TARGET_BYTES / 2:
        p = mid_note; mid_done = True
    body.append(p); size += len(p)
prompt = head + "".join(body) + tail
(OUT / "truth.json").write_text(json.dumps({"vault": vault, "paging": paging, "bytes": len(prompt.encode())}))
print(NAME, "prompt bytes", len(prompt.encode()), flush=True)

if TOOL == "agy":
    cmd = ["agy", "--mode", "plan", "--model", "gemini-3.8-flash-medium", "--input-format", "stream-json",
           "--output-format", "stream-json", "--print", ""]
    stdin = json.dumps({"event": "user", "message": {"content": prompt}}) + "\n"
else:
    cmd = ["claude", "-p", "--model", "haiku", "--disallowedTools", "Bash", "--output-format", "stream-json", "--verbose"]
    stdin = prompt

t0 = time.time()
r = subprocess.run(cmd, input=stdin, capture_output=True, text=True, cwd=WS, timeout=1500)
(OUT / "out.ndjson").write_text(r.stdout); (OUT / "err.txt").write_text(r.stderr)

calls, result, events = [], None, []
for line in r.stdout.splitlines():
    try: d = json.loads(line)
    except Exception: continue
    if TOOL == "agy":
        su = d.get("step_update") or {}
        if su.get("step_type") == "agent_response" and su.get("usage"):
            u = su["usage"]; calls.append(u.get("input_tokens", 0) + u.get("cache_read_tokens", 0))
        if su.get("step_type") in ("checkpoint", "system_message") and su.get("state") == "DONE": events.append(su["step_type"])
        if d.get("event") == "result": result = d["result"]
    else:
        if d.get("type") == "assistant":
            u = d["message"].get("usage", {}); calls.append(u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0))
        if d.get("subtype") == "compact_boundary": events.append("compact_boundary")
        if d.get("type") == "result": result = d
resp = (result or {}).get("response") or (result or {}).get("result") or ""
summary = {"name": NAME, "secs": round(time.time() - t0), "exit": r.returncode, "calls_context": calls, "events": events,
           "status": (result or {}).get("status") or (result or {}).get("subtype"), "is_error": (result or {}).get("is_error"),
           "error": (result or {}).get("error"), "response": resp[:800], "stderr": r.stderr[:500],
           "truth": {"vault": vault, "paging": paging}, "vault_ok": vault in resp, "paging_ok": bool(re.search(rf"(?<![\w-]){paging}(?![\w-])", resp))}
(OUT / "summary.json").write_text(json.dumps(summary, indent=1))
print(json.dumps({k: v for k, v in summary.items() if k != "truth"}, indent=1)[:1800])
