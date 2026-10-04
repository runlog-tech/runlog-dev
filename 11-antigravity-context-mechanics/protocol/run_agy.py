#!/usr/bin/env python3
"""agy side of video 19. Usage: run_agy.py <rep> [--control]. Resumable; stops cleanly on quota errors."""
import json, subprocess, sys, time
from pathlib import Path
import protocol as P

REP = sys.argv[1]; CONTROL = "--control" in sys.argv
NAME = f"agy-{'control' if CONTROL else 'rep'}{REP}"
WS = Path("/home/invii/retest-work") / NAME
OUT = Path(__file__).parent / "receipts" / NAME
OUT.mkdir(parents=True, exist_ok=True)
MODEL = "gemini-3.8-flash-medium"
MAX_FILLER, POST_FILLER = 16, 2

if not (WS / ".truth.json").exists():
    P.make_workspace(WS, int(REP) * 7 + 3 + (500 if CONTROL else 0), "agy")
truth = json.loads((WS / ".truth.json").read_text())
state_f = OUT / "state.json"
state = json.loads(state_f.read_text()) if state_f.exists() else {"conv": None, "turns": []}
def save(): state_f.write_text(json.dumps(state, indent=1))

def run_turn(label, prompt):
    for t in state["turns"]:
        if t["label"] == label: return t
    cmd = ["agy", "--output-format", "stream-json", "--mode", "accept-edits", "--model", MODEL]
    if state["conv"]: cmd.append(f"--conversation={state['conv']}")
    cmd.append(f"--print={prompt} Work only inside {WS} (use absolute paths under it).")
    t0 = time.time()
    r = subprocess.run(cmd, cwd=WS, capture_output=True, text=True, timeout=1500)
    (OUT / f"{len(state['turns']):02d}-{label}.ndjson").write_text(r.stdout)
    (OUT / f"{len(state['turns']):02d}-{label}.err").write_text(r.stderr)
    if "RESOURCE_EXHAUSTED" in r.stdout + r.stderr:
        print("QUOTA", (r.stdout + r.stderr)[-300:]); save(); sys.exit(3)
    calls, tools, resp = [], 0, ""
    for ln in r.stdout.splitlines():
        try: e = json.loads(ln)
        except Exception: continue
        if e.get("event") == "step_update":
            s = e["step_update"]
            if s.get("conversation_id") and not state["conv"]: state["conv"] = s["conversation_id"]
            if s.get("step_type") == "tool" and s.get("state") == "DONE": tools += 1
            if s.get("step_type") == "agent_response" and s.get("state") == "DONE" and s.get("usage"):
                u = s["usage"]
                calls.append({"step": s.get("step_index"), "input": (u.get("input_tokens") or 0) + (u.get("cache_read_tokens") or 0),
                              "fresh": u.get("input_tokens"), "cache_read": u.get("cache_read_tokens"), "out": u.get("output_tokens")})
        if e.get("event") == "result":
            res = e["result"]; resp = res.get("response", ""); state["conv"] = state["conv"] or res.get("conversation_id")
    t = {"label": label, "prompt": prompt, "response": resp, "calls": calls, "tool_steps": tools, "secs": round(time.time() - t0)}
    state["turns"].append(t); save()
    print(f"{label}: calls={[c['input'] for c in calls]} tools={tools} {t['secs']}s resp={resp[:70]!r}", flush=True)
    return t

def dropped():
    seq = [c["input"] for t in state["turns"] for c in t["calls"] if c["input"]]
    return any(b < 0.7 * a for a, b in zip(seq, seq[1:])), seq

run_turn("T1-setup", P.T1)
for i in range(3): run_turn(f"T{i+2}-feature{i+1}", P.feature_turn(i))
if not CONTROL:
    n = 0
    while n < MAX_FILLER and not dropped()[0]:
        n += 1; run_turn(f"F{n:02d}", P.filler_turn(n))
    comp = dropped()[0]
    for j in range(POST_FILLER): run_turn(f"F{n+j+1:02d}-post", P.filler_turn(n + j + 1))
    state["compaction_observed"] = comp; state["fillers_before_drop"] = n; save()
ans, tools = {}, {}
for key, prompt in P.PROBES:
    t = run_turn(f"P-{key}", prompt); ans[key] = t["response"]; tools[key] = t["tool_steps"]
state["scores_auto"] = P.score(WS, {**{k: ans.get(k, "") for k in ("M3", "M4", "M4B", "M5", "M6")}}, tools, truth)
state["filler_ok"] = {t["label"]: (truth.get(f"spec{int(t['label'][1:3])}_sec12","~") in t["response"]) for t in state["turns"] if t["label"].startswith("F")}; state["truth"] = {k: v for k, v in truth.items() if not k.startswith("spec")}
dr, seq = dropped(); state["context_curve"] = seq; state["drop_seen"] = dr; save()
print(json.dumps(state["scores_auto"], indent=1)); print("curve", seq); print("DONE", NAME)
