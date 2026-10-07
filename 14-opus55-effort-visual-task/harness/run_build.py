"""Same facts, two model/effort settings: produce video 21's sections 04 and 05 end to end (script, TTS, alignment, frames, render).
Usage: python3 run_build.py <arm> <model> <effort>   e.g. A claude-sonnet-5-5 medium | B claude-opus-5-5 low
Work dir /tmp/yt-build/<arm>/work is a copy of mods-handoff-test with sections 04/05 removed (script text, builders, audio, frames).
context-meter logs 5h/weekly % per turn; a watchdog kills the run past the stop rules.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
ROUND2 = os.getenv("BUILD_ROUND") == "2"
SRC = Path("~/faceless-yt-transformation/scripts/mods-handoff-test")
FACTS = Path("~/faceless-yt-transformation/scripts/claude-code-mods-audit")
MOD = Path("~/faceless-yt-transformation/scripts/you-should-know-test/mods/context-meter")
OUT = Path(os.getenv("BUILD_OUT", "/tmp/yt-build"))
FIVE_STOP = int(os.getenv("BUILD_5H_STOP", "80"))
WEEK_RISE_STOP = int(os.getenv("BUILD_WEEK_RISE_STOP", "10"))
TOOLS = ["Read", "Edit", "Write", "Bash"]
DENY = ["Bash(rm:*)", "Bash(sudo:*)", "Bash(git push:*)", "Bash(git commit:*)", "Bash(mv:*)"]

PROMPT_R1 = """You are producing two sections of a YouTube video for the RUNLOG channel: Section 04 "Result One, The Bill" and Section 05 "Result Two, The Rules" of video 21. The test results are in facts/ (PILOT_RESULTS.md, NOTES.md). Read HOUSE_RULES.md first.
Do the whole job, in this order:
1. script.md: write the Section 04 and Section 05 blocks (Visual Direction + Narration, same format as the other sections; stubs with headers are in place). About 50 to 60 seconds of narration each. Read the other sections for voice and format.
2. TTS: `python3 generate_tts.py` (local Kokoro on CPU; it lints banned words), then `python3 run_alignments.py` for word timings.
3. Frames: add `sec04()` and `sec05()` to hyperframes/sections.py using the helpers in hyperframes/fb.py and the other sections as patterns; `python3 hyperframes/sections.py 04 05`. Real exhibit files are in assets/exhibits/.
4. Verify each with `python3 hyperframes/render_section.py <section-id> check`, look at snapshots (`python3 hyperframes/render_section.py <section-id> snap 5,20,35,48`, PNGs in hyperframes/snapshots/), fix what you find.
5. Render each: `python3 hyperframes/render_section.py <section-id> render` (section ids: 04-result-one-the-bill, 05-result-two-the-rules).
Run commands from this directory. Finish with a 5-line summary of what you produced and anything you could not verify."""

PROMPT_R2 = PROMPT_R1.replace('3. Frames: add `sec04()` and `sec05()` to hyperframes/sections.py using the helpers in hyperframes/fb.py and the other sections as patterns; `python3 hyperframes/sections.py 04 05`. Real exhibit files are in assets/exhibits/.', '3. Frames: design sections 04 and 05 however you judge best. hyperframes/sections.py, fb.py and the other sections are optional reference; you may add `sec04()`/`sec05()` there (`python3 hyperframes/sections.py 04 05` writes the frame HTML) or write your own HyperFrames composition at hyperframes/compositions/frames/<section-id>.html. Real exhibit files are in assets/exhibits/.')
PROMPT = PROMPT_R2 if ROUND2 else PROMPT_R1


def strip_section(text: str, num: str) -> str:
    m = re.search(rf"(## Section {num}:[^\n]*\n(?:- [^\n]*\n)*)(.*?)(?=\n---\n|\n## Section |\Z)", text, re.S)
    head = "\n".join(l for l in m.group(1).splitlines() if not l.startswith("- **Duration"))
    return text.replace(m.group(0), head + "\n\n(TO WRITE)\n")


def meter_rows(d: Path, name: str = "meter.jsonl") -> list[dict]:
    f = d / name
    return [json.loads(l) for l in f.read_text().splitlines() if l.strip()] if f.exists() else []


def pct(r: dict, kind: str) -> int:
    return next((x["percentUsed"] for x in r["rateLimits"] if x["kind"] == kind), 0)


def live_limits(events: Path) -> tuple[int | None, int | None]:
    """Latest 5h and weekly percent from the rate_limit_event rows in the recorded stream."""
    five = week = None
    for l in events.read_text().splitlines():
        if '"rate_limit_event"' in l:
            w = json.loads(l)["rate_limit_info"].get("unifiedWindows", {})
            five = round(w["five_hour"]["utilization"] * 100) if "five_hour" in w else five
            week = round(w["seven_day"]["utilization"] * 100) if "seven_day" in w else week
    return five, week


def main(arm: str, model: str, effort: str) -> None:
    busy = subprocess.run(["pgrep", "-f", "^claude -p You are"], capture_output=True, text=True).stdout.split()
    if busy:
        raise SystemExit(f"another build agent is running: {busy}")
    d = OUT / arm
    if d.exists():
        raise SystemExit(f"{d} exists")
    w = d / "work"
    shutil.copytree(SRC, w, ignore=shutil.ignore_patterns("renders", "snapshots", "__pycache__", "node_modules", "out", "short", "*.mp4", "*-alignment.json", "captions.srt", "upload-notes.md", "assemble_video21.py", "build_receipts.sh", "render"))
    for sid in ("04-result-one-the-bill", "05-result-two-the-rules"):
        for f in (w / "hyperframes" / "audio").glob(f"{sid}*"):
            f.unlink()
        (w / "hyperframes" / "compositions" / "frames" / f"{sid}.html").unlink(missing_ok=True)
    # alignments for the untouched sections are regenerated by run_alignments.py; keep the shipped ones out so arms cannot copy timing
    s = (w / "script.md").read_text()
    s = strip_section(strip_section(s, "04"), "05")
    (w / "script.md").write_text(s)
    code = (w / "hyperframes" / "sections.py").read_text()
    code = re.sub(r"def sec04\(\):.*?(?=\n\ndef sec06)", "", code, flags=re.S)
    code = code.replace('["01", "02", "03", "04", "05", "06", "07"]', '["01", "02", "03", "06", "07"]')
    (w / "hyperframes" / "sections.py").write_text(code)
    (w / "facts").mkdir()
    for f in ("PILOT_RESULTS.md", "NOTES.md"):
        shutil.copy(FACTS / f, w / "facts" / f)
    shutil.copy(HERE / ("HOUSE_RULES_R2.md" if ROUND2 else "HOUSE_RULES.md"), w / "HOUSE_RULES.md")
    if ROUND2:  # no scripted pauses: one Kokoro call per section, the voice handles its own pacing
        g = (w / "generate_tts.py").read_text()
        g = g.replace("BEATS: dict[str, dict] = {**_auto_beats(), **OVERRIDES}", "BEATS: dict[str, dict] = {}")
        g = g.replace("    words = text.split()\n    ends = set(", "    return [text]\n    words = text.split()\n    ends = set(", 1)
        (w / "generate_tts.py").write_text(g)
    env = {**os.environ, "CI": "1"}
    env.pop("CLAUDE_CODE_CHILD_SESSION", None)
    base_log = d / "base.jsonl"
    subprocess.run(["claude", "-p", "ok", "--model", "haiku", "--plugin-dir", str(MOD)], cwd=d, env={**env, "CONTEXT_METER_LOG": str(base_log)}, capture_output=True, timeout=180)
    base = meter_rows(d, "base.jsonl")[-1]
    base5, basew = pct(base, "five_hour"), pct(base, "seven_day")
    t0 = time.time()
    (d / "meta.json").write_text(json.dumps({"arm": arm, "model": model, "effort": effort, "start": t0, "5h_before": base5, "week_before": basew}))
    proc = subprocess.Popen(["claude", "-p", PROMPT, "--model", model, "--effort", effort, "--output-format", "stream-json", "--verbose", "--plugin-dir", str(MOD),
                             "--permission-mode", "acceptEdits", "--allowedTools", *TOOLS, "--disallowedTools", *DENY],
                            cwd=w, env={**env, "CONTEXT_METER_LOG": str(d / "meter.jsonl")}, stdout=open(d / "events.jsonl", "w"), stderr=open(d / "stderr.log", "w"))
    stopped = False
    while proc.poll() is None:
        time.sleep(15)
        five, week = live_limits(d / "events.jsonl")
        if five is not None and (five >= FIVE_STOP or week - basew >= WEEK_RISE_STOP):
            proc.kill()
            stopped = True
            break
    r = meter_rows(d)
    last = r[-1] if r else base
    (d / "summary.json").write_text(json.dumps({"turns": len(r), "5h_before": base5, "5h_after": pct(last, "five_hour"), "week_before": basew, "week_after": pct(last, "seven_day"),
                                                "wall_s": round(time.time() - t0), "stopped_by_rule": stopped, "meter_cost_usd": (last.get("cost") or {}).get("usd")}))


if __name__ == "__main__":
    main(*sys.argv[1:4])
