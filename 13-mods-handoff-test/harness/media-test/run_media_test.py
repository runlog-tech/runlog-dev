"""Does /compact keep an image or a long prompt? Three setups on Sonnet 5.5, n reps each, headless claude -p turns.
IMG   : image saved on disk, Claude reads it (the image enters the conversation), /compact, then asks for details.
INLINE: a long spec pasted into the chat, /compact, then asks for details.
FILE  : the same spec saved to spec.md and Claude told to read it, /compact, then asks for details.
Records the answer, how many model turns the question took (>1 means it went back to a tool, e.g. re-read the file), and a regex grade.
Usage: python3 run_media_test.py [reps]"""

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
OUT = Path(os.getenv("MEDIA_OUT", "/tmp/mods-media-test"))
MODEL = os.getenv("PILOT_MODEL", "sonnet")

FACTS = {  # label -> (value shown in the spec, regex that must match the answer)
    "codename": ("Kestrel", r"Kestrel"), "port": ("4817", r"4817"), "retention": ("19 days", r"\b19\b"),
    "owner": ("Mina Okafor", r"Okafor"), "timeout": ("2750 ms", r"2,?750"), "branch": ("release/q4-lantern", r"q4-lantern"),
    "cache": ("384 MB", r"\b384\b"), "region": ("eu-north-3", r"eu-north-3"), "rollback": ("ZX-4410", r"ZX-?4410"),
    "retries": ("6", r"\b(6|six)\b"), "loglevel": ("WARN", r"WARN"), "sprint": ("S-52", r"S-?52"),
}
FILLER = [
    "The nightly job starts shortly after midnight and walks the list of customer accounts in alphabetical order, skipping any account that has been flagged as dormant by the finance team.",
    "For each account it requests the latest invoices from the upstream ledger, compares the totals with what was stored the night before, and records any difference in a staging table.",
    "When the upstream ledger is slow, the job should not block the rest of the run; it moves on, remembers the account, and comes back to it at the end of the pass.",
    "Operators have asked for a quieter log, because the old version wrote one line per invoice and nobody read them, so only unusual events should appear in normal operation.",
    "The summary written at the end lists how many accounts were processed, how many were skipped, and how many needed a second attempt, followed by the slowest five accounts.",
    "Several customers use custom billing calendars, so the job must never assume that a month has a fixed number of days or that invoices are numbered without gaps.",
    "Money is always stored as integer minor units, never as floating point, and every conversion to a display string happens at the very edge of the system.",
    "Support staff occasionally re-run a single account by hand, so the job must be safe to run twice in a row without creating duplicate staging rows.",
]
def _spec() -> str:
    facts = [
        f"The service codename is {FACTS['codename'][0]}.", f"It listens on port {FACTS['port'][0]}.",
        f"Staging rows are kept for {FACTS['retention'][0]} before cleanup.", f"The owner to ask about changes is {FACTS['owner'][0]}.",
        f"Upstream calls time out after {FACTS['timeout'][0]}.", f"Work happens on the branch {FACTS['branch'][0]}.",
        f"The in-memory cache is capped at {FACTS['cache'][0]}.", f"The service runs in region {FACTS['region'][0]}.",
        f"The emergency rollback token is {FACTS['rollback'][0]}.", f"A failed pull is retried at most {FACTS['retries'][0]} times.",
        f"Normal log level is {FACTS['loglevel'][0]}.", f"This belongs to sprint {FACTS['sprint'][0]}.",
    ]
    paras = []
    for i in range(36):
        body = " ".join(FILLER[(i + j) % len(FILLER)] for j in range(3))
        if i % 3 == 1 and facts:
            body += " " + facts.pop(0)
        paras.append(body)
    return "Project brief for the billing sync service. Please keep the specific details exactly, I will ask about them later.\n\n" + "\n\n".join(paras) + "\n\n" + " ".join(facts) + "\n\nNothing needs to be built yet."
SPEC = _spec()
IMG_FACTS = {"order": r"7731", "red": r"\bred\b", "blue": r"\bblue\b", "green": r"\bgreen\b", "date": r"14\s*Nov"}

Q_MEM = " Answer from memory only. Do not use any tools and do not open any files; if you do not remember something, say so."
TURNS_FILLER = "Create util.py with a one-line function reverse(s) that returns the string reversed. Reply in one line."
Q_SPEC = "From the brief I gave you earlier, list all twelve details (codename, port, retention, owner, timeout, branch, cache, region, rollback token, retries, log level, sprint)."
Q_IMG = "In the image order.png, what is the order number, the colors of the three shapes, and the ship-by date?"


def make_image(path: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont
    im = Image.new("RGB", (900, 500), "white")
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 60)
    s = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 36)
    d.text((40, 30), "ORDER 7731", fill="black", font=f)
    d.ellipse((60, 160, 260, 360), fill=(220, 40, 40)); d.text((130, 380), "A", fill="black", font=s)
    d.rectangle((340, 160, 540, 360), fill=(40, 70, 220)); d.text((420, 380), "B", fill="black", font=s)
    d.polygon([(720, 360), (620, 160), (820, 160)], fill=(30, 160, 60)); d.text((700, 380), "C", fill="black", font=s)
    d.text((40, 440), "Ship by 14 Nov", fill="black", font=s)
    im.save(path)


def turn(arm: str, label: str, prompt: str, sid: str, new: bool, work: Path) -> dict:
    cmd = ["claude", "-p", "--model", MODEL, "--permission-mode", "acceptEdits", "--output-format", "json", "--session-id" if new else "-r", sid, prompt]
    t0 = time.time()
    r = subprocess.run(cmd, cwd=work, capture_output=True, text=True, timeout=900)
    try:
        res = json.loads(r.stdout)
    except Exception:
        res = {"result": r.stdout[-500:], "error": r.stderr[-500:]}
    (OUT / arm / "turns").mkdir(parents=True, exist_ok=True)
    (OUT / arm / "turns" / f"{label}.json").write_text(json.dumps(res, indent=1))
    print(f"{arm} {label}: {time.time() - t0:.0f}s turns={res.get('num_turns')} cost=${res.get('total_cost_usd')}", flush=True)
    return res


def grade(arm: str, text: str) -> dict:
    pats = IMG_FACTS if arm.startswith("IMG") else {k: v[1] for k, v in FACTS.items()}
    hit = {k: bool(re.search(p, text, re.I)) for k, p in pats.items()}
    return {"hit": sum(hit.values()), "of": len(hit), "missing": [k for k, v in hit.items() if not v]}


def run(kind: str, rep: int) -> dict:
    arm = f"{kind}{rep}"
    work = OUT / arm / "work"
    shutil.rmtree(OUT / arm, ignore_errors=True)
    work.mkdir(parents=True)
    sid = str(uuid.uuid4())
    if kind == "IMG":
        make_image(work / "order.png")
        turn(arm, "t1", "Open the image order.png in this folder with the Read tool and say 'seen' when you have looked at it.", sid, True, work)
        q = Q_IMG
    elif kind == "INLINE":
        turn(arm, "t1", SPEC + "\n\nReply with the single word 'noted'.", sid, True, work)
        q = Q_SPEC
    else:
        (work / "spec.md").write_text(SPEC)
        turn(arm, "t1", "Read spec.md in this folder with the Read tool and say 'noted' when done.", sid, True, work)
        q = Q_SPEC
    turn(arm, "t2", TURNS_FILLER, sid, False, work)
    turn(arm, "compact", "/compact", sid, False, work)
    rm = turn(arm, "q_memory", q + Q_MEM, sid, False, work)
    rn = turn(arm, "q_natural", q, sid, False, work)
    gm, gn = grade(arm, rm.get("result", "")), grade(arm, rn.get("result", ""))
    summary = {"arm": arm, "memory": gm, "natural": gn, "natural_turns": rn.get("num_turns"), "answer_memory": rm.get("result", "")[:1500], "answer_natural": rn.get("result", "")[:1500]}
    (OUT / arm / "summary.json").write_text(json.dumps(summary, indent=1))
    print(f"== {arm}: from memory {gm['hit']}/{gm['of']} missing={gm['missing']} | natural {gn['hit']}/{gn['of']} turns={rn.get('num_turns')}", flush=True)
    return summary


if __name__ == "__main__":
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    OUT.mkdir(parents=True, exist_ok=True)
    for rep in range(1, reps + 1):
        for kind in ("IMG", "INLINE", "FILE"):
            run(kind, rep)
