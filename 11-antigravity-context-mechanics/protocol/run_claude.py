#!/usr/bin/env python3
"""Claude Code side of video 19. Usage: run_claude.py <rep> [--control]. Same markers/filler as run_agy.py, manual /compact."""
import json, subprocess, sys, time, uuid
from pathlib import Path
import protocol as P

REP = sys.argv[1]; CONTROL = "--control" in sys.argv
NAME = f"claude-{'control' if CONTROL else 'rep'}{REP}"
WS = Path("/home/invii/retest-work") / NAME
OUT = Path(__file__).parent / "receipts" / NAME
OUT.mkdir(parents=True, exist_ok=True)
MODEL = "haiku"; PRE_FILLER, POST_FILLER = 8, 2

if not (WS / ".truth.json").exists():
    P.make_workspace(WS, int(REP) * 7 + 3 + (500 if CONTROL else 0), "claude")
truth = json.loads((WS / ".truth.json").read_text())
state_f = OUT / "state.json"
state = json.loads(state_f.read_text()) if state_f.exists() else {"sid": str(uuid.uuid4()), "turns": [], "started": False}
def save(): state_f.write_text(json.dumps(state, indent=1))

def run_turn(label, prompt):
    for t in state["turns"]:
        if t["label"] == label: return t
    cmd = ["claude", "-p", "--model", MODEL, "--permission-mode", "acceptEdits", "--disallowedTools", "Bash",
           "--output-format", "stream-json", "--verbose"]
    cmd += ["-r", state["sid"]] if state["started"] else ["--session-id", state["sid"]]
    cmd.append(prompt if prompt.startswith("/") else f"{prompt} Work only inside {WS} (use absolute paths under it).")
    t0 = time.time()
    r = subprocess.run(cmd, cwd=WS, capture_output=True, text=True, timeout=1500)
    (OUT / f"{len(state['turns']):02d}-{label}.ndjson").write_text(r.stdout)
    (OUT / f"{len(state['turns']):02d}-{label}.err").write_text(r.stderr)
    low = (r.stdout + r.stderr).lower()
    if "usage limit" in low or "rate limit" in low or "limit reached" in low:
        print("QUOTA", low[-300:]); save(); sys.exit(3)
    state["started"] = True
    calls, tools, resp, boundary, seen = [], 0, "", None, set()
    for ln in r.stdout.splitlines():
        try: e = json.loads(ln)
        except Exception: continue
        if e.get("type") == "assistant":
            m = e.get("message", {}); u = m.get("usage") or {}
            if u and m.get("id") not in seen:
                seen.add(m.get("id")); calls.append({"input": (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0), "out": u.get("output_tokens")})
            tools += sum(1 for c in m.get("content", []) if isinstance(c, dict) and c.get("type") == "tool_use")
        if e.get("type") == "system" and "compact" in json.dumps(e).lower() and e.get("subtype") != "init": boundary = e
        if e.get("type") == "result": resp = e.get("result", "") or ""
    t = {"label": label, "prompt": prompt, "response": resp, "calls": calls, "tool_steps": tools, "secs": round(time.time() - t0), "compact_event": boundary}
    state["turns"].append(t); save()
    print(f"{label}: calls={[c['input'] for c in calls]} tools={tools} {t['secs']}s resp={resp[:70]!r}", flush=True)
    return t

run_turn("T1-setup", P.T1)
for i in range(3): run_turn(f"T{i+2}-feature{i+1}", P.feature_turn(i))
if not CONTROL:
    for n in range(1, PRE_FILLER + 1): run_turn(f"F{n:02d}", P.filler_turn(n))
    run_turn("COMPACT", "/compact")
    for j in range(POST_FILLER): run_turn(f"F{PRE_FILLER+j+1:02d}-post", P.filler_turn(PRE_FILLER + j + 1))
ans, tools = {}, {}
for key, prompt in P.PROBES:
    t = run_turn(f"P-{key}", prompt); ans[key] = t["response"]; tools[key] = t["tool_steps"]
state["scores_auto"] = P.score(WS, {k: ans.get(k, "") for k in ("M3", "M4", "M4B", "M5", "M6")}, tools, truth)
state["filler_ok"] = {t["label"]: (truth.get(f"spec{int(t['label'][1:3])}_sec12","~") in t["response"]) for t in state["turns"] if t["label"].startswith("F")}; state["truth"] = {k: v for k, v in truth.items() if not k.startswith("spec")}
state["context_curve"] = [c["input"] for t in state["turns"] for c in t["calls"]]; save()
print(json.dumps(state["scores_auto"], indent=1)); print("curve", state["context_curve"]); print("DONE", NAME)
