"""Builds facts.json and FACTS_TABLES.md from data/<round>/<arm>/ (events.jsonl.gz, meta.json, frames/*.html, script.md).
Usage: python3 facts.py    (no quota; reads local files and ffprobe on /tmp wavs when present)
"""

import collections
import gzip
import json
import re
import statistics
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
TMP = {"r1": "/tmp/yt-build", "r2": "/tmp/yt-build2", "r3": "/tmp/yt-frames", "r3b": "/tmp/yt-frames-b"}
LABEL = {("claude-sonnet-5-5", "medium"): "Sonnet medium", ("claude-sonnet-5-5", "high"): "Sonnet high", ("claude-opus-5-5", "low"): "Opus low",
         ("claude-opus-5-5", "medium"): "Opus medium", ("claude-opus-5-5", "high"): "Opus high"}
KEY_FIGURES = {"$0.95 no reset": r"0?\.95|ninety[- ]five", "$1.20 subagent": r"1\.20|1\.2\b|dollar (and )?twenty", "$0.53 /compact": r"0?\.53|fifty[- ]three",
               "$0.57 brief": r"0?\.57|fifty[- ]seven", "$0.66 mod": r"0?\.66|sixty[- ]six", "$0.73 mod": r"0?\.73|seventy[- ]three"}
BORDER = re.compile(r"border:\s*[0-9.]+px")


def load_events(arm_dir: Path) -> list[dict]:
    with gzip.open(arm_dir / "events.jsonl.gz", "rt") as f:
        return [json.loads(l) for l in f if l.strip()]


def phase_of(blocks: list[dict]) -> str:
    for b in blocks:
        if b.get("type") != "tool_use":
            continue
        inp = b.get("input") or {}
        cmd, path = inp.get("command", "") or "", inp.get("file_path", "") or ""
        if b["name"] == "Bash" and re.search(r"generate_tts|run_alignments|align_captions", cmd):
            return "tts"
        if b["name"] == "Bash" and re.search(r"render_section|hyperframes (render|check|snap)|ffmpeg|render", cmd):
            return "render"
        if b["name"] in ("Write", "Edit") and path.endswith("script.md"):
            return "script"
        if b["name"] in ("Write", "Edit") and ("frames/" in path or path.endswith(".html") or path.endswith("sections.py")):
            return "frames"
    return "other"


def run_facts(rnd: str, arm_dir: Path) -> dict:
    meta = json.loads((arm_dir / "meta.json").read_text())
    ev = load_events(arm_dir)
    res = next((e for e in reversed(ev) if e["type"] == "result"), {})
    mu = res.get("modelUsage") or {}
    tok = {k: sum(v.get(k2, 0) for v in mu.values()) for k, k2 in (("input", "inputTokens"), ("cache_write", "cacheCreationInputTokens"),
                                                                   ("cache_read", "cacheReadInputTokens"), ("output", "outputTokens"), ("thinking", "thinkingTokens"))}
    rl = [e["rate_limit_info"].get("unifiedWindows", {}) for e in ev if e["type"] == "rate_limit_event"]
    pct = lambda w, k: round(w[k]["utilization"] * 100) if k in w else None
    msgs: dict[str, dict] = {}
    for e in ev:
        m = e.get("message") or {}
        if e["type"] == "assistant" and m.get("usage") and m.get("id"):
            d = msgs.setdefault(m["id"], {"usage": m["usage"], "blocks": {}})
            for i, b in enumerate(m.get("content", [])):
                d["blocks"][b.get("id") or f"{b.get('type')}{i}"] = b
    phase_turns, phase_in = collections.Counter(), collections.Counter()
    for d in msgs.values():
        u = d["usage"]
        ph = phase_of(list(d["blocks"].values()))
        phase_turns[ph] += 1
        phase_in[ph] += u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
    dur = round((res.get("duration_ms") or 0) / 1000)
    return {"round": rnd, "arm": meta["arm"], "label": LABEL[(meta["model"], meta["effort"])], "model": meta["model"], "effort": meta["effort"],
            "turns": res.get("num_turns"), "tokens": tok, "cost_usd": round(res.get("total_cost_usd") or 0, 2), "duration_s": dur,
            "out_tok_per_s": round(tok["output"] / dur, 1) if dur else None,
            "meter_5h": [pct(rl[0], "five_hour"), pct(rl[-1], "five_hour")] if rl else None,
            "meter_week": [pct(rl[0], "seven_day"), pct(rl[-1], "seven_day")] if rl else None,
            "meta_5h_before": meta.get("5h_before"), "is_error": res.get("is_error"),
            "phase_turns": dict(phase_turns), "phase_input_tokens": dict(phase_in)}


def frame_metrics(arm_dir: Path) -> dict | None:
    f = arm_dir / "frames" / "04-result-one-the-bill.html"
    if not f.exists():
        return None
    h = f.read_text()
    px = [float(x) for x in re.findall(r"font-size:\s*([0-9.]+)px", h)]
    return {"decls": len(px), "min": min(px), "median": statistics.median(px), "max": max(px), "under_40": sum(p < 40 for p in px),
            "ge_84": sum(p >= 84 for p in px), "border_decls": len(BORDER.findall(h)), "em_en_dashes": h.count("—") + h.count("–")}


def section_narration(script: str, num: str) -> str:
    m = re.search(rf"^## Section {num}:.*?### Narration:\s*(.*?)(?=^---|^## Section|\Z)", script, re.S | re.M)
    return m.group(1).strip() if m else ""


def wav_seconds(path: Path) -> float | None:
    if not path.exists():
        return None
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    return round(float(out.stdout.strip()), 1) if out.stdout.strip() else None


def script_facts(rnd: str, arm_dir: Path) -> dict | None:
    sp = arm_dir / "script.md"
    if not sp.exists() or rnd not in ("r1", "r2"):
        return None
    script, rows = sp.read_text(), {}
    for num, stem in (("04", "04-result-one-the-bill"), ("05", "05-result-two-the-rules")):
        n = section_narration(script, num)
        if not n:
            continue
        words, sents = len(n.split()), len(re.findall(r"[.!?](\s|$)", n))
        secs = wav_seconds(Path(TMP[rnd]) / arm_dir.name / "work/hyperframes/audio" / f"{stem}.wav")
        rows[num] = {"words": words, "sentences": sents, "audio_s": secs, "wpm": round(words / secs * 60) if secs else None,
                     "em_en_dashes": n.count("—") + n.count("–"),
                     "key_figures_present": [k for k, rx in KEY_FIGURES.items() if re.search(rx, n, re.I)] if num == "04" else None}
    return rows


def main() -> None:
    runs, frames, scripts = [], {}, {}
    for rd in sorted(DATA.iterdir()):
        for ad in sorted(rd.iterdir()):
            runs.append(run_facts(rd.name, ad))
            fm = frame_metrics(ad)
            if fm:
                frames[f"{rd.name}/{ad.name}"] = fm
            sf = script_facts(rd.name, ad)
            if sf:
                scripts[f"{rd.name}/{ad.name}"] = sf
    (ROOT / "facts.json").write_text(json.dumps({"runs": runs, "frames": frames, "scripts": scripts}, indent=2))
    lines = ["| Round/arm | Setup | Turns | Output | Thinking | Cache read | Cache write | Cost | Wall s | out tok/s | 5h meter | Weekly |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in runs:
        t = r["tokens"]
        m5 = f"{r['meter_5h'][0]} to {r['meter_5h'][1]}" if r["meter_5h"] else "n/a"
        mw = f"{r['meter_week'][0]} to {r['meter_week'][1]}" if r["meter_week"] else "n/a"
        lines.append(f"| {r['round']}/{r['arm']} | {r['label']} | {r['turns']} | {t['output']:,} | {t['thinking']:,} | {t['cache_read']/1e6:.2f}M | {t['cache_write']/1e3:.0f}K | ${r['cost_usd']:.2f} | {r['duration_s']} | {r['out_tok_per_s']} | {m5} | {mw} |")
    (ROOT / "FACTS_TABLES.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("\nFRAMES")
    for k, v in frames.items():
        print(k, v)
    print("\nSCRIPTS")
    for k, v in scripts.items():
        print(k, v)
    print("\nPHASES (turns / input-side tokens)")
    for r in runs:
        tot = sum(r["phase_input_tokens"].values()) or 1
        print(f"{r['round']}/{r['arm']} {r['label']}:", {p: f"{r['phase_turns'][p]}t/{round(100 * r['phase_input_tokens'][p] / tot)}%" for p in r["phase_turns"]})


if __name__ == "__main__":
    main()
