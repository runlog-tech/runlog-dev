"""Round 3: write ONE HyperFrames frame from scratch (no fb.py, no sections.py, no earlier frames) for frozen narration, audio and direction.
Usage: python3 run_frames.py <arm> <model> <effort>
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import run_build as rb

HERE = Path(__file__).parent
FROZEN = Path("/tmp/yt-frames/frozen")
OUT = Path(os.getenv("FRAMES_OUT", "/tmp/yt-frames"))
DESIGN = os.getenv("FRAMES_DESIGN") == "1"  # round 3b: give the channel design system document
SID = "04-result-one-the-bill"

PROMPT = """You are building one frame of a YouTube video for the RUNLOG channel: Section 04, "Result One, The Bill". Read HOUSE_RULES.md first.
Work, in this order:
1. Read HOUSE_RULES.md and, if present, docs/DESIGN_SYSTEM.md in full. Then read script.md (the narration, and the visual direction as a starting brief), facts/ (the test results), the real exhibit files in assets/exhibits/, and hyperframes/render_section.py plus the word timings in hyperframes/audio/04-result-one-the-bill-alignment.json.
2. Write the frame as your own HyperFrames HTML composition at hyperframes/compositions/frames/04-result-one-the-bill.html (the file is mounted into the video by render_section.py). Time beats to the spoken words using the alignment file. No helper library is provided; use hyperframes docs and your own judgment.
3. Verify: `python3 hyperframes/render_section.py 04-result-one-the-bill check`, then snapshots (`python3 hyperframes/render_section.py 04-result-one-the-bill snap 5,20,35,50`, PNGs in hyperframes/snapshots/). Fix what you find.
4. Render: `python3 hyperframes/render_section.py 04-result-one-the-bill render`.
Run commands from this directory. Finish with a 5-line summary of what you built and anything you could not verify."""


def main(arm: str, model: str, effort: str) -> None:
    busy = subprocess.run(["pgrep", "-f", "^claude -p You are"], capture_output=True, text=True).stdout.split()
    if busy:
        raise SystemExit(f"another agent is running: {busy}")
    d = OUT / arm
    if d.exists():
        raise SystemExit(f"{d} exists")
    w = d / "work"
    (w / "hyperframes" / "audio").mkdir(parents=True)
    (w / "hyperframes" / "compositions" / "frames").mkdir(parents=True)
    for f in ("hyperframes.json", "package.json", "render_section.py"):
        shutil.copy(rb.SRC / "hyperframes" / f, w / "hyperframes" / f)
    for f in (f"{SID}.wav", f"{SID}-alignment.json"):
        shutil.copy(FROZEN / f, w / "hyperframes" / "audio" / f)
    shutil.copytree(rb.SRC / "assets" / "exhibits", w / "assets" / "exhibits")
    (w / "facts").mkdir()
    for f in ("PILOT_RESULTS.md", "NOTES.md"):
        shutil.copy(rb.FACTS / f, w / "facts" / f)
    shutil.copy(HERE / ("HOUSE_RULES_R3B.md" if DESIGN else "HOUSE_RULES_R3.md"), w / "HOUSE_RULES.md")
    if DESIGN:
        (w / "docs").mkdir()
        shutil.copy("~/faceless-yt-transformation/docs/DESIGN_SYSTEM.md", w / "docs" / "DESIGN_SYSTEM.md")
    (w / "script.md").write_text("## Section 04: Result One, The Bill\n- **Top Badge:** `RESULT 01` | `THE BILL`\n\n### Visual Direction:\n" + (FROZEN / "visual_direction.md").read_text() + "\n\n### Narration:\n" + (FROZEN / "narration.txt").read_text() + "\n")
    env = {**os.environ, "CI": "1"}
    env.pop("CLAUDE_CODE_CHILD_SESSION", None)
    subprocess.run(["claude", "-p", "ok", "--model", "haiku", "--plugin-dir", str(rb.MOD)], cwd=d, env={**env, "CONTEXT_METER_LOG": str(d / "base.jsonl")}, capture_output=True, timeout=180)
    base = rb.meter_rows(d, "base.jsonl")[-1]
    basew = rb.pct(base, "seven_day")
    t0 = time.time()
    (d / "meta.json").write_text(json.dumps({"arm": arm, "model": model, "effort": effort, "start": t0, "5h_before": rb.pct(base, "five_hour"), "week_before": basew}))
    proc = subprocess.Popen(["claude", "-p", PROMPT, "--model", model, "--effort", effort, "--output-format", "stream-json", "--verbose", "--plugin-dir", str(rb.MOD),
                             "--permission-mode", "acceptEdits", "--allowedTools", *rb.TOOLS, "--disallowedTools", *rb.DENY],
                            cwd=w, env={**env, "CONTEXT_METER_LOG": str(d / "meter.jsonl")}, stdout=open(d / "events.jsonl", "w"), stderr=open(d / "stderr.log", "w"))
    stopped = False
    while proc.poll() is None:
        time.sleep(15)
        five, week = rb.live_limits(d / "events.jsonl")
        if week is not None and week - basew >= rb.WEEK_RISE_STOP:
            proc.kill()
            stopped = True
            break
    (d / "summary.json").write_text(json.dumps({"wall_s": round(time.time() - t0), "stopped_by_rule": stopped}))


if __name__ == "__main__":
    main(*sys.argv[1:4])
