"""Does a rule introduced mid-session survive /compact, versus the same rule in CLAUDE.md? Headless claude -p, n reps per model.
CHAT   : the rule is stated in chat at turn 2 (mid-session), applied once, then /compact, then a new task that should follow it.
CLAUDEMD: the same rule sits in CLAUDE.md from the start, never stated in chat, same turns.
Grade: does the reply after /compact still start with the tag? (v1 used a code comment rule; the file kept the pattern visible, so it was confounded and is kept only as a note.)
Usage: python3 run_midrule_test.py <model> [reps]"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

OUT = Path(os.getenv("MID_OUT", "/tmp/mods-midrule-test"))
RULE = "Start every reply with the exact tag [RL-7731] and then your answer."
MODEL = sys.argv[1] if len(sys.argv) > 1 else "sonnet"


def turn(arm, label, prompt, sid, new, work):
    cmd = ["claude", "-p", "--model", MODEL, "--permission-mode", "acceptEdits", "--output-format", "json", "--session-id" if new else "-r", sid, prompt]
    t0 = time.time()
    r = subprocess.run(cmd, cwd=work, capture_output=True, text=True, timeout=900)
    try:
        res = json.loads(r.stdout)
    except Exception:
        res = {"result": r.stdout[-500:]}
    (OUT / arm / "turns").mkdir(parents=True, exist_ok=True)
    (OUT / arm / "turns" / f"{label}.json").write_text(json.dumps(res, indent=1))
    print(f"{arm} {label}: {time.time() - t0:.0f}s cost=${res.get('total_cost_usd')}", flush=True)
    return res


def run(kind, rep):
    """Reply-format rule (leaves no trace in any file, so only memory or CLAUDE.md can carry it)."""
    arm = f"{MODEL}-{kind}{rep}"
    work = OUT / arm / "work"
    shutil.rmtree(OUT / arm, ignore_errors=True)
    work.mkdir(parents=True)
    sid = str(uuid.uuid4())
    one = " Answer in one short sentence."
    if kind == "CLAUDEMD":
        (work / "CLAUDE.md").write_text("# Project rules\n- " + RULE + "\n")
        turn(arm, "t1", "What does Python's str.upper do?" + one, sid, True, work)
        turn(arm, "t2", "What does Python's str.lower do?" + one, sid, False, work)
    else:
        turn(arm, "t1", "What does Python's str.upper do?" + one, sid, True, work)
        turn(arm, "t2", "New rule for the rest of this session: " + RULE + " Now: what does Python's str.lower do?" + one, sid, False, work)
    pre = turn(arm, "t3", "What does Python's str.title do?" + one, sid, False, work)
    turn(arm, "compact", "/compact", sid, False, work)
    post = turn(arm, "q", "What does Python's str.strip do?" + one, sid, False, work)
    tag = "[RL-7731]"
    summary = {"arm": arm, "before_compact_has_tag": tag in pre.get("result", "")[:20], "after_compact_has_tag": tag in post.get("result", "")[:20], "pre": pre.get("result", ""), "post": post.get("result", "")}
    (OUT / arm / "summary.json").write_text(json.dumps(summary, indent=1))
    print(f"== {arm}: before {summary['before_compact_has_tag']} after {summary['after_compact_has_tag']} | {post.get('result', '')[:80]!r}", flush=True)


if __name__ == "__main__":
    reps = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    OUT.mkdir(parents=True, exist_ok=True)
    for rep in range(1, reps + 1):
        for kind in ("CHAT", "CLAUDEMD"):
            run(kind, rep)
