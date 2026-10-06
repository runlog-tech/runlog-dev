"""Does a PASTED image (a real image block in the user message, no file path) survive /compact? Sonnet 5.5, n reps per setup.
PASTE_SILENT: image pasted with 'reply with the single word seen' (the assistant never describes it), /compact, then asked from memory.
PASTE_DESCRIBED: image pasted and the assistant is asked to describe it in one sentence first, /compact, then asked from memory.
Answers are graded for the five image facts. No file with the image exists in the work folder, so nothing can be re-read.
Usage: python3 run_paste_test.py <model> [reps]"""

import base64
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

import importlib.util
_s = importlib.util.spec_from_file_location("rm", Path(__file__).parent / "run_media_test.py")
rm = importlib.util.module_from_spec(_s); _s.loader.exec_module(rm)

OUT = Path(os.getenv("PASTE_OUT", "/tmp/mods-paste-test"))
MODEL = sys.argv[1] if len(sys.argv) > 1 else "sonnet"
Q = "From the image I pasted earlier: what is the order number, the colors of the three shapes, and the ship-by date? Answer from memory only. Do not use any tools and do not open any files; if you do not remember something, say so."


def first_turn(arm, kind, sid, work):
    png = work.parent / "order.png"  # kept outside the work folder so it cannot be re-read
    rm.make_image(png)
    b = base64.b64encode(png.read_bytes()).decode()
    text = "Reply with the single word 'seen'." if kind == "PASTE_SILENT" else "Describe this image in one sentence."
    msg = {"type": "user", "message": {"role": "user", "content": [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b}}, {"type": "text", "text": text}]}}
    r = subprocess.run(["claude", "-p", "--model", MODEL, "--permission-mode", "acceptEdits", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose", "--session-id", sid],
                       input=json.dumps(msg) + "\n", cwd=work, capture_output=True, text=True, timeout=600)
    last = [json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")][-1]
    (OUT / arm / "turns").mkdir(parents=True, exist_ok=True)
    (OUT / arm / "turns" / "t1.json").write_text(json.dumps(last, indent=1))
    print(f"{arm} t1: result={str(last.get('result'))[:80]!r}", flush=True)


def turn(arm, label, prompt, sid, work):
    r = subprocess.run(["claude", "-p", "--model", MODEL, "--permission-mode", "acceptEdits", "--output-format", "json", "-r", sid, prompt], cwd=work, capture_output=True, text=True, timeout=600)
    try:
        res = json.loads(r.stdout)
    except Exception:
        res = {"result": r.stdout[-500:]}
    (OUT / arm / "turns" / f"{label}.json").write_text(json.dumps(res, indent=1))
    print(f"{arm} {label}: ok", flush=True)
    return res


def run(kind, rep):
    arm = f"{MODEL}-{kind}{rep}"
    shutil.rmtree(OUT / arm, ignore_errors=True)
    work = OUT / arm / "work"
    work.mkdir(parents=True)
    sid = str(uuid.uuid4())
    first_turn(arm, kind, sid, work)
    turn(arm, "t2", rm.TURNS_FILLER, sid, work)
    turn(arm, "compact", "/compact", sid, work)
    res = turn(arm, "q", Q, sid, work)
    hit = {k: bool(re.search(p, res.get("result", ""), re.I)) for k, p in rm.IMG_FACTS.items()}
    summary = {"arm": arm, "hit": sum(hit.values()), "of": len(hit), "missing": [k for k, v in hit.items() if not v], "answer": res.get("result", "")[:800]}
    (OUT / arm / "summary.json").write_text(json.dumps(summary, indent=1))
    print(f"== {arm}: {summary['hit']}/{summary['of']} missing={summary['missing']} | {res.get('result', '')[:120]!r}", flush=True)


if __name__ == "__main__":
    reps = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    OUT.mkdir(parents=True, exist_ok=True)
    for rep in range(1, reps + 1):
        for kind in ("PASTE_SILENT", "PASTE_DESCRIBED"):
            run(kind, rep)
