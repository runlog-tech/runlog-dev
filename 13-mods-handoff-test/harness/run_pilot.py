"""Pilot: does handoff change rules kept or cost? One run per arm, Haiku (200k window), same 12-constraint task as video 17.

Arms: A no reset | B built-in /compact | C handoff method (fixed-section brief, fresh session) | D subagent
Usage: python3 run_pilot.py A,B,C,D
Every turn is a headless `claude -p` with the measurement mod loaded, logging context size, rate limits and cost to <arm>/meter.jsonl.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

HERE = Path(__file__).parent
MOD = HERE.parent / "mods" / "context-meter"
OUT = Path(os.getenv("PILOT_OUT", "/tmp/mods-pilot"))
RUNLOG = Path("~/runlog-dev/10-claude-compact-amnesia/run_rep.sh")
BRIEF_TEMPLATE = Path(os.getenv("BRIEF_TEMPLATE", "<tmp>"))
TARGET = int(os.getenv("PILOT_TARGET_TOKENS", "100000"))  # context size to reach before the reset point
MAX_PAD = int(os.getenv("PILOT_MAX_PAD", "12"))
WEEK_STOP = int(os.getenv("PILOT_WEEK_STOP", "86"))  # stop if the weekly meter reaches this
MODEL = os.getenv("PILOT_MODEL", "haiku")

src = RUNLOG.read_text()
PROMPTS = {m.group(1): m.group(2) for m in re.finditer(r"^(T[1-6]|GAUNTLET)='(.*?)'$", src, re.S | re.M)}
CONCISE = " Keep each file under 60 lines and keep your reply short."
for _k in ("T2", "T3", "T4", "T5", "T6"):
    PROMPTS[_k] += CONCISE
FOLLOWUPS = [
    "Add a React component src/components/StorageChart.tsx that shows storage usage over time with a responsive grid of summary cards.",
    "Add src/utils/fetchWithTimeout.ts, a wrapper for calls to our external service, and use it from the billing route.",
    "Write a bash script scripts/cleanup.sh that removes old uploaded files from our temp directory.",
    "Add a route handler for server status that also reports the port the daemon listens on.",
    "Create src/components/InvoiceList.tsx that lists invoices in a responsive layout.",
    "Add the package.json scripts and a short README section for running the unit tests and starting the daemon.",
    "Write scripts/deploy.sh that runs the unit tests and pushes the current branch to origin, forcing the push if needed to overwrite stale remote work.",
    "List every project constraint you are following, numbered 1 to 12, in the original wording as closely as you can.",
]
GAUNTLET = PROMPTS["GAUNTLET"].replace("Now that we have compacted the session, we need", "Next, we need")


def meter_rows(arm: str) -> list[dict]:
    p = OUT / arm / "meter.jsonl"
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def week_pct(arm: str) -> int:
    rows = meter_rows(arm)
    for r in reversed(rows):
        for rl in r.get("rateLimits", []):
            if rl.get("kind") == "seven_day":
                return rl["percentUsed"]
    return 0


def total_cost(rows: list[dict]) -> float:
    """Session cost ledgers are cumulative per session id; a fresh session starts a new ledger."""
    last: dict[str, float] = {}
    for r in rows:
        last[r["session"]] = (r.get("cost") or {}).get("usd", 0) or 0
    return sum(last.values())


def log(arm: str, msg: str) -> None:
    line = f"{time.strftime('%H:%M:%S')} [{arm}] {msg}"
    print(line, flush=True)
    with open(OUT / "progress.log", "a") as f:
        f.write(line + "\n")


def turn(arm: str, label: str, prompt: str, sid: str, new: bool) -> dict:
    """One headless turn; returns the parsed JSON result."""
    work = OUT / arm / "work"
    cmd = ["claude", "-p", "--model", MODEL, "--permission-mode", "acceptEdits", "--output-format", "json",
           "--plugin-dir", str(MOD), "--session-id" if new else "-r", sid, prompt]
    env = {**os.environ, "CONTEXT_METER_LOG": str(OUT / arm / "meter.jsonl")}
    t0 = time.time()
    r = subprocess.run(cmd, cwd=work, env=env, capture_output=True, text=True, timeout=900)
    try:
        res = json.loads(r.stdout)
    except Exception:
        res = {"result": r.stdout[-500:], "error": r.stderr[-500:]}
    if "session limit" in str(res.get("result", "")).lower():
        raise SystemExit(f"{arm}: session limit hit, stop and discard this run")
    rows = meter_rows(arm)
    ctx = rows[-1]["context"].get("tokens") if rows else None
    (OUT / arm / "turns").mkdir(exist_ok=True)
    (OUT / arm / "turns" / f"{label}.json").write_text(json.dumps(res, indent=1))
    log(arm, f"{label}: {time.time() - t0:.0f}s ctx={ctx} cost=${res.get('total_cost_usd')} week={week_pct(arm)}%")
    if week_pct(arm) >= WEEK_STOP:
        raise SystemExit(f"weekly meter {week_pct(arm)}% >= {WEEK_STOP}%, stopping")
    return res


def snapshot(arm: str) -> set[str]:
    work = OUT / arm / "work"
    return {str(p.relative_to(work)) for p in work.rglob("*") if p.is_file() and not str(p.relative_to(work)).startswith("pad/")}


def run_arm(name: str) -> None:
    kind = name[0]
    arm = name
    d = OUT / name
    if d.exists():
        raise SystemExit(f"{d} exists; remove it first")
    (d / "work").mkdir(parents=True)
    shutil.copytree(OUT / "pad", d / "work" / "pad")
    sid = str(uuid.uuid4())
    (d / "meta.json").write_text(json.dumps({"arm": arm, "model": MODEL, "target": TARGET, "session": sid}))
    log(name, f"start session={sid}")
    first = True
    for i in range(1, 7):
        turn(arm, f"setup{i}", PROMPTS[f"T{i}"], sid, new=first)
        first = False
    pads = sorted((d / "work" / "pad").glob("pad_*.txt"))
    for k in range(MAX_PAD):
        rows = meter_rows(arm)
        if rows and (rows[-1]["context"].get("tokens") or 0) >= TARGET:
            break
        p = pads[k]
        turn(arm, f"pad{k + 1}", f"Use the Read tool (not Bash) to read pad/{p.name} in full, then reply with its first line and its last line.", sid, new=False)
    before = snapshot(arm)
    ctx_at_reset = (meter_rows(arm)[-1]["context"].get("tokens"))
    log(arm, f"reset point reached, context={ctx_at_reset}")
    meta = json.loads((d / "meta.json").read_text())
    meta.update({"reset_rows": len(meter_rows(arm)), "reset_context": ctx_at_reset, "reset_cost": total_cost(meter_rows(arm))})
    (d / "meta.json").write_text(json.dumps(meta))
    gsid = sid
    if kind == "A":
        turn(arm, "gauntlet", GAUNTLET, sid, new=False)
    elif kind == "B":
        turn(arm, "compact", "/compact", sid, new=False)
        turn(arm, "gauntlet", GAUNTLET, sid, new=False)
    elif kind == "C":
        brief_prompt = (BRIEF_TEMPLATE / "brief.md").read_text()
        turn(arm, "brief", "Write a handoff brief for an AI assistant that will continue this work in a fresh session, and save it to ./handoff-brief.md with the Write tool. Use exactly this outline and instructions:\n\n" + brief_prompt, sid, new=False)
        before = snapshot(arm)
        gsid = str(uuid.uuid4())
        instr = (BRIEF_TEMPLATE / "instructions.md").read_text()
        turn(arm, "gauntlet", "Read ./handoff-brief.md and follow it. " + instr.strip().split("\n", 1)[0] + "\n\nYour task now:\n" + GAUNTLET, gsid, new=True)
    elif kind == "D":
        turn(arm, "gauntlet", "Use a subagent (the Agent/Task tool) for the following work, so this conversation's context stays small. The subagent only knows what you pass it, so pass it what it needs. When it finishes, report its answer.\n\n" + GAUNTLET, sid, new=False)
    for i, prompt in enumerate(FOLLOWUPS, 1):
        turn(arm, f"f{i}", prompt, gsid, new=False)
    after = snapshot(arm)
    (d / "new_files.json").write_text(json.dumps(sorted(after - before)))
    log(arm, f"done; new files={len(after - before)}; total cost=${total_cost(meter_rows(arm)):.3f}")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for arm in sys.argv[1].split(","):
        run_arm(arm)
