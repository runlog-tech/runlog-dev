"""Drives a real community handoff mod in an interactive claude session (pexpect pty). Usage: python3 run_mod.py <mod-plugin-dir> <name>  e.g. claude-auto-handoff H1
The mod, not the harness, decides when to hand off (threshold env). Same prompts, pads and follow-ups as run_pilot.py; meter rows come from context-meter.
"""

import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

import pexpect

import run_pilot as rp

OUT = rp.OUT
THRESHOLD = os.getenv("MOD_THRESHOLD", "100000")


def did_reset(r):
    """A new session id (/clear mods) or a context drop of 30%+ from its running peak (in-place compaction mods)."""
    if len({x["session"] for x in r}) > 1:
        return True
    peak = 0
    for x in r:
        t = x["context"].get("tokens") or 0
        if peak >= 0.5 * int(THRESHOLD) and t < 0.7 * peak:
            return True
        peak = max(peak, t)
    return False


def rows(name):
    return rp.meter_rows(name)


def wait_turn(child, name, before, timeout=420):
    """Wait for a new meter row, then for the screen to go quiet."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            child.expect(pexpect.TIMEOUT, timeout=2)
        except pexpect.EOF:
            raise SystemExit("claude exited")
        scr = re.sub(r"\x1b\[[0-9;?<>=]*[A-Za-z]|\x1b[()][A-Z0-9]|\x1b\][^\x07]*\x07", "", Path(child.logfile_read.name).read_text(errors="ignore")[-6000:])[-1500:]
        if ("❯1.Yes" in scr.replace(" ", "")[-600:] or "❯ 1. Yes" in scr[-600:]) and time.time() - getattr(wait_turn, "t", 0) > 6:
            child.send("1\r")  # Bash prompts appear even in acceptEdits; the cwd is a throwaway dir
            wait_turn.t = time.time()
        if len(rows(name)) > before:
            time.sleep(4)
            try:
                child.expect(pexpect.TIMEOUT, timeout=3)
            except pexpect.EOF:
                pass
            return
    raise SystemExit(f"timeout waiting for turn in {name}")


def extract_replies(d: Path, name: str) -> None:
    """Writes turns/gauntlet.json, turns/f8.json and new_files.json in the shape grade.py reads, from the saved transcripts."""
    proj = Path.home() / ".claude" / "projects" / ("-" + str(d / "work").strip("/").replace("/", "-").replace("_", "-").replace(".", "-"))
    texts = {}
    for f in sorted(proj.glob("*.jsonl"), key=lambda p: p.stat().st_mtime):
        lines = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
        want = None
        for m in lines:
            msg = m.get("message") or {}
            c = msg.get("content")
            if m.get("type") == "user":
                t = c if isinstance(c, str) else " ".join(b.get("text", "") for b in c if isinstance(b, dict))
                if not t.strip():
                    continue  # a tool_result turn, not a new prompt: keep collecting the reply
                want = "gauntlet" if t.startswith("Next, we need") or "User Billing" in t[:200] else ("f8" if "List every project constraint" in t else None)
            elif m.get("type") == "assistant" and want and isinstance(c, list):
                t = " ".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
                if t.strip():
                    texts[want] = texts.get(want, "") + t
    for k, v in texts.items():
        (d / "turns" / f"{k}.json").write_text(json.dumps({"result": v}))
    files = [str(p.relative_to(d / "work")) for p in (d / "work").rglob("*") if p.is_file() and not str(p.relative_to(d / "work")).startswith(("pad/", ".claude/"))]
    (d / "new_files.json").write_text(json.dumps(sorted(files)))
    rp.log(name, f"extracted replies: {sorted(texts)}; files={len(files)}")


def main(mod: str, name: str) -> None:
    d = OUT / name
    if d.exists():
        raise SystemExit(f"{d} exists")
    (d / "work" / ".claude").mkdir(parents=True)
    shutil.copytree(OUT / "pad", d / "work" / "pad")
    (d / "work" / ".claude" / "settings.local.json").write_text(json.dumps({"pluginConfigs": {os.getenv("MOD_NAME", "auto-handoff"): {"options": json.loads(os.getenv("MOD_OPTIONS", '{"viewer": ""}'))}}}))
    env = {**os.environ, "CONTEXT_METER_LOG": str(d / "meter.jsonl"), "AUTO_HANDOFF_TOKENS": THRESHOLD, "FORCE_COLOR": "0", "CLAUDE_CODE_FORCE_SESSION_PERSISTENCE": "1"}
    env.pop("CLAUDE_CODE_CHILD_SESSION", None)
    child = pexpect.spawn("claude", ["--model", os.getenv("PILOT_MODEL", "haiku"), "--permission-mode", "acceptEdits", "--plugin-dir", str(rp.MOD), "--plugin-dir", mod],
                          cwd=d / "work", env=env, encoding="utf-8", dimensions=(50, 200), timeout=30)
    (d / "meta.json").write_text(json.dumps({"arm": "C-real", "mod": mod, "threshold": THRESHOLD}))
    log = open(d / "screen.log", "w")
    child.logfile_read = log
    time.sleep(8)
    child.send("\x1b[B")
    time.sleep(1)
    child.send("\r")
    time.sleep(8)
    prompts = [rp.PROMPTS[f"T{i}"] for i in range(1, 7)]
    for k in range(1, 17):
        prompts.append(f"Use the Read tool (not Bash) to read pad/pad_{k:02d}.txt in full, then reply with its first line and its last line.")
    prompts += [rp.GAUNTLET] + rp.FOLLOWUPS
    sessions = set()
    handed = False
    for i, p in enumerate(prompts):
        if 6 <= i < 22 and did_reset(rows(name)):
            continue  # first handoff happened: stop padding, go to the gauntlet
        r = rows(name)
        ctx = (r[-1]["context"].get("tokens") or 0) if r else 0
        if i >= 6 and not handed and did_reset(r):
            handed = True
        if i >= 6 and not handed and ctx >= int(THRESHOLD) * 1.05 and len(r) and not did_reset(r):
            # past threshold with no handoff yet: give the mod time to act
            time.sleep(60)
            r = rows(name)
            sessions = {x["session"] for x in r}
            if did_reset(r):
                handed = True
        if handed and not (d / "meta.json").read_text().count("reset_cost"):
            meta = json.loads((d / "meta.json").read_text())
            meta.update({"reset_rows": len(r), "reset_context": ctx, "reset_cost": rp.total_cost(r)})
            (d / "meta.json").write_text(json.dumps(meta))
        before = len(rows(name))
        child.send(p.replace("\n", " ") )
        time.sleep(1)
        child.send("\r")
        wait_turn(child, name, before)
        r = rows(name)
        sessions = {x["session"] for x in r}
        rp.log(name, f"turn{i}: ctx={(r[-1]['context'].get('tokens') or 0)} sessions={len(sessions)} cost=${rp.total_cost(r):.3f}")
        if rp.week_pct(name) >= rp.WEEK_STOP:
            raise SystemExit("weekly stop")
        if handed and i >= len(prompts) - len(rp.FOLLOWUPS) - 1 and i == len(prompts) - 1:
            break
    (d / "turns").mkdir(exist_ok=True)
    child.send("/exit\r")
    time.sleep(3)
    extract_replies(d, name)
    log.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
