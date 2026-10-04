#!/usr/bin/env python3
"""Bisect the Claude (haiku) 'Prompt is too long' threshold by prompt bytes. Sequential."""
import json, subprocess, sys
from pathlib import Path
lo, hi = int(sys.argv[1]), int(sys.argv[2])   # lo known/assumed OK, hi known too long
def run(n):
    subprocess.run(["python3", "run_big.py", "claude", str(n)], capture_output=True, text=True, timeout=1500)
    s = json.load(open(f"receipts/big-claude-{n}/summary.json"))
    ok = not s["is_error"]
    print(n, "OK" if ok else "TOO LONG", s["calls_context"], "vault_ok", s["vault_ok"], "paging_ok", s["paging_ok"], repr(s["response"][:60]), flush=True)
    return ok
print("check lo", lo, flush=True)
if not run(lo): print("lo already too long"); sys.exit()
while hi - lo > 20000:
    mid = (lo + hi) // 2
    if run(mid): lo = mid
    else: hi = mid
print("threshold between", lo, "and", hi)
