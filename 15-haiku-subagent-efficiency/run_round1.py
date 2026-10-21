#!/usr/bin/env python3
"""Round 1 runner (PLAN.md). Usage: python3 run_round1.py T1:L0 [T2:L1 ...] | all
Results: /tmp/subagent-eff/results.jsonl (one row per run) and /tmp/subagent-eff/runs/<task>_<cond>/."""
import glob, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import briefs

HERE = Path(__file__).parent
REPO = HERE.parent.parent
OUT = Path(os.getenv("EFF_OUT", "/tmp/subagent-eff"))
FIX = Path("/tmp/subagent-fixture")
MOD = REPO / "scripts/claude-code-mods-audit/mods/context-meter"
BUDGET = float(os.getenv("EFF_BUDGET", "10"))
WEEK_STOP = 0  # no weekly stop (user removed the 86% rule 2026-10-17); the budget cap is the only stop
sys.path.insert(0, str(REPO / "scripts/_tools/runlog-guard"))
from subagent_ledger import summarize  # noqa: E402


def fixture() -> None:
    if FIX.exists():
        return
    subprocess.run(["git", "worktree", "add", "-q", "--detach", str(FIX), "HEAD"], cwd=REPO, check=True)
    for p in (".claude", "CLAUDE.md", "AGENTS.md", "memory"):
        t = FIX / p
        shutil.rmtree(t) if t.is_dir() else t.unlink(missing_ok=True)
    big()


def big() -> None:
    """T6 input: a copy of memory/video_ideas.md (about 347 KB) outside memory/ so the fixture stays free of project memory."""
    (FIX / "notes").mkdir(exist_ok=True)
    if not (FIX / "notes/video_ideas.md").exists():
        shutil.copy(REPO / "memory/video_ideas.md", FIX / "notes/video_ideas.md")


def agent_md(c: dict) -> str:
    front = ["---", "name: worker", "description: Worker subagent for delegated tasks.", f"model: {c['model']}", f"effort: {c['effort']}"]
    if c["tools"]:
        front.append(f"tools: {c['tools']}")
    return "\n".join(front + ["---", "", c["prompt"], ""])


def run_one(task: str, cond: str) -> dict:
    d = OUT / "runs" / f"{task}_{cond}"
    if d.exists():
        raise SystemExit(f"{d} exists")
    d.mkdir(parents=True)
    c = briefs.condition(cond, task)
    cwd = d / "work" if task in ("T4", "R1") else FIX
    cwd.mkdir(exist_ok=True)
    if task == "R1":
        shutil.copytree(HERE / "render_task/scaffold", cwd, dirs_exist_ok=True)
    (cwd / ".claude/agents").mkdir(parents=True, exist_ok=True)
    (cwd / ".claude/agents/worker.md").write_text(agent_md(c))
    (d / "brief.txt").write_text(c["brief"])
    (d / "agent.md").write_text(agent_md(c))
    parent = ("You are a dispatcher. Call the Agent tool exactly once with subagent_type \"worker\" and prompt set to the text between the BRIEF markers, copied exactly. "
              "Do nothing else. When it returns, reply with only: DONE\n<<<BRIEF\n" + c["brief"] + "\nBRIEF>>>")
    env = {**os.environ, "CONTEXT_METER_LOG": str(d / "meter.jsonl")}
    cmd = ["claude", "-p", "--model", briefs.SONNET, "--effort", "low", "--permission-mode", "acceptEdits", "--output-format", "json",
           "--allowedTools", "Agent", "Read", "Grep", "Glob", "Bash", "Write", "Edit", "--plugin-dir", str(MOD), parent]
    t0 = time.time()
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=1200)
    wall = time.time() - t0
    try:
        res = json.loads(r.stdout)
    except Exception:
        res = {"result": r.stdout[-400:], "error": r.stderr[-400:]}
    (d / "result.json").write_text(json.dumps(res, indent=1))
    sid = res.get("session_id")
    tr = glob.glob(os.path.expanduser(f"~/.claude/projects/*/{sid}/subagents/agent-*.jsonl")) if sid else []
    info, report = {}, ""
    if tr:
        shutil.copy(tr[0], d / "subagent.jsonl")
        info = {**(summarize(tr[0]) or {}), **norm_cost(tr[0])}
        for line in open(tr[0]):
            try:
                m = json.loads(line).get("message") or {}
            except ValueError:
                continue
            if m.get("role") == "assistant" and isinstance(m.get("content"), list):
                txt = "".join(b.get("text", "") for b in m["content"] if b.get("type") == "text")
                if txt.strip():
                    report = txt
    (d / "report.txt").write_text(report)
    mu = res.get("modelUsage") or {}
    sub = mu.get(c["model"]) or {}
    total = res.get("total_cost_usd") or 0
    row = {"task": task, "cond": cond, "model": c["model"], "effort": c["effort"], "wall_s": round(wall), "total_cost": round(total, 4),
           "parent_cost": round(total - (sub.get("costUSD") or 0), 4), "sub_cost": sub.get("costUSD"), "sub_in": sub.get("inputTokens"), "sub_cache_read": sub.get("cacheReadInputTokens"),
           "sub_cache_write": sub.get("cacheCreationInputTokens"), "sub_out": sub.get("outputTokens"), **{f"tr_{k}": v for k, v in info.items()},
           "report_chars": len(report), "norm_cost": info.get("norm_cost") if c["model"] == briefs.HAIKU else None, "turns_over_100k": info.get("turns_over_100k"), "week": week_pct(d / "meter.jsonl")}
    row.update(score(task, d, report, cwd))
    with open(OUT / "results.jsonl", "a") as f:
        f.write(json.dumps(row) + "\n")
    return row


PRICES = {False: {"in": 0.10, "out": 0.50, "cw": 0.125, "cr": 0.01}, True: {"in": 0.50, "out": 2.50, "cw": 0.625, "cr": 0.05}}  # Haiku 5.5 per M tokens, up to / over 100K (Anthropic page)


def norm_cost(path: str) -> dict:
    """Cold-start cost from token counts: turn 1 prompt is a cache write, each later turn reads the previous prompt and writes the new tokens; tier by prompt size (Amendment 1)."""
    prev = total = over = 0
    for line in open(path):
        try:
            m = json.loads(line).get("message") or {}
        except ValueError:
            continue
        u = m.get("usage")
        if m.get("role") != "assistant" or not u:
            continue
        prompt = u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
        hi = prompt > 100000
        over += hi
        pr = PRICES[hi]
        read = min(prev, prompt)
        total += (read * pr["cr"] + (prompt - read) * pr["cw"] + u.get("output_tokens", 0) * pr["out"]) / 1e6
        prev = prompt
    return {"norm_cost": round(total, 5), "turns_over_100k": over}


def week_pct(p: Path) -> int | None:
    if not p.exists():
        return None
    for l in reversed(p.read_text().splitlines()):
        for rl in json.loads(l).get("rateLimits", []):
            if rl.get("kind") == "seven_day":
                return rl["percentUsed"]
    return None


def truth_t1() -> set[tuple[str, int]]:
    o = subprocess.run(["git", "grep", "-n", "meter.jsonl", "--", "scripts/*.py"], cwd=FIX, capture_output=True, text=True).stdout
    return {(m.group(1), int(m.group(2))) for m in re.finditer(r"^([^:]+):(\d+):", o, re.M)}


def truth_t3() -> dict[str, tuple[bool, bool]]:
    out = {}
    for f in sorted(FIX.glob("scripts/*/upload-notes.md")):
        t = f.read_text()
        out[f.parent.name] = (bool(re.search(r"Primary[^\n]*?`[^`]+`", t)), bool(re.search(r"^## Tags\s*$", t, re.M)))
    return out


MUST = {"cost_100_130": r"0\.19|0\.20|0\.21|\$0\.2", "cost_default": r"1\.0\d|\$1\b", "rule_loss_low": r"(100K|130K)", "ok_200_default": r"200K",
        "claude_md": r"CLAUDE\.md", "n3": r"n\s*=\s*3|three runs|3 runs|per setup|per arm", "no_400k": r"400K", "tier_vs_tokens": r"(price|tier|cost per)"}


def score(task: str, d: Path, report: str, cwd: Path) -> dict:
    if task == "T1":
        truth = truth_t1()
        rep = {(re.sub(r"^.*?(scripts/)", r"\1", m.group(1)), int(m.group(2))) for m in re.finditer(r"([\w./\-]+\.py)[:\s#L(]*(\d+)", report)}
        hit = lambda p, l, tp, tl: tl == l and (tp == p or tp.endswith("/" + p))  # a reported path may be a suffix of the full path
        matched = sum(any(hit(p, l, tp, tl) for tp, tl in truth) for p, l in rep)
        covered = sum(any(hit(p, l, tp, tl) for p, l in rep) for tp, tl in truth)
        return {"t1_truth": len(truth), "t1_reported": len(rep), "t1_precision": round(matched / len(rep), 3) if rep else 0, "t1_recall": round(covered / len(truth), 3), "t1_made_up": len(rep) - matched}
    if task == "T2":
        doc = (FIX / "scripts/autocompact-window-test/RESULTS.md").read_text()
        got = [k for k, rx in MUST.items() if re.search(rx, report, re.I)]
        nums = set(re.findall(r"\$?\d[\d,.]*[KkMm%]?", report)) - set(re.findall(r"\$?\d[\d,.]*[KkMm%]?", doc))
        nums = {n.rstrip(".,") for n in nums if n.rstrip(".,")}
        return {"t2_facts": len(got), "t2_missing": sorted(set(MUST) - set(got)), "t2_numbers_not_in_doc": sorted(nums)[:12], "t2_bullets": len(re.findall(r"^\s*[-*•\d]", report, re.M))}
    if task == "T3":
        truth = truth_t3()
        want_fail = {k for k, (p, t) in truth.items() if not (p and t)}
        exact = 0
        for k, (p, t) in truth.items():
            m = re.search(rf"{re.escape(k)}\S*\s*:?\s*.*?primary\s*=\s*(yes|no).*?tags\s*=\s*(yes|no)", report, re.I)
            exact += bool(m and (m.group(1).lower() == "yes") == p and (m.group(2).lower() == "yes") == t)
        fail_words = r"fail|missing|\bno\b|false|absent|✗|❌"
        said_fail = {k for k in truth if any(k in ln and re.search(fail_words, ln, re.I) for ln in report.splitlines())}
        return {"t3_folders": len(truth), "t3_exact_format_match": exact, "t3_truth_failing": len(want_fail), "t3_said_failing_approx": len(said_fail), "t3_failing_overlap_approx": len(said_fail & want_fail)}
    if task == "T5":
        truth = truth_t5()
        ok_t = ok_s = 0
        for k, (title, status) in truth.items():
            lines = [ln for ln in report.splitlines() if k in ln]
            ln = lines[0].lower() if lines else ""
            ok_t += bool(title) and norm(title)[:30] in norm(ln)
            ok_s += ("none" in ln.split("|")[-1]) if status == "none" else (norm(status)[:25] in norm(ln))
        return {"t5_folders": len(truth), "t5_title_ok": ok_t, "t5_status_ok": ok_s, "t5_with_status": sum(1 for v in truth.values() if v[1] != "none")}
    if task == "T6":
        got = [k for k, rx in T6_MUST.items() if re.search(rx, report, re.I)]
        return {"t6_facts": len(got), "t6_total": len(T6_MUST), "t6_missing": sorted(set(T6_MUST) - set(got)), "t6_bullets": len(re.findall(r"^\s*[-*\u2022\d]", report, re.M))}
    if task == "R1":
        return score_r1(d, cwd)
    if task == "T4":
        sol, tst = cwd / "solution.py", cwd / "test_solution.py"
        hidden = d / "hidden_test.py"
        hidden.write_text(HIDDEN)
        shutil.copy(sol, d / "solution_copy.py") if sol.exists() else None
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(hidden)], cwd=cwd, capture_output=True, text=True, timeout=120)
        passed = int(m.group(1)) if (m := re.search(r"(\d+) passed", r.stdout)) else 0
        own = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "test_solution.py"], cwd=cwd, capture_output=True, text=True, timeout=120) if tst.exists() else None
        loc = sum(len([l for l in p.read_text().splitlines() if l.strip()]) for p in (sol, tst) if p.exists())
        return {"t4_hidden_passed": passed, "t4_hidden_total": 12, "t4_own_tests_ok": (own.returncode == 0) if own else None, "t4_loc": loc, "t4_sol_loc": len([l for l in sol.read_text().splitlines() if l.strip()]) if sol.exists() else 0}
    return {}


def score_r1(d: Path, cwd: Path) -> dict:
    """Render task: check passes, an mp4 exists at 1920x1080 and about 6 s, the four values and the title are in the HTML, the last second is not blank."""
    html = (cwd / "index.html").read_text() if (cwd / "index.html").exists() else ""
    vals = sum(v in html for v in ("0.051", "0.068", "0.197", "0.153"))
    sep = r"\s*(?:to|-|\u2013|\u2014)\s*"
    labels = sum(bool(re.search(l, html, re.I)) for l in (rf"\b0{sep}50K", rf"\b50{sep}100K", rf"\b100{sep}150K", rf"\b150{sep}250K"))
    fonts = [float(x) for x in re.findall(r"font-size:\s*([\d.]+)px", html)]
    chk = subprocess.run(["npm", "exec", "--yes", "--", "hyperframes@0.8.82", "check"], cwd=cwd, env={**os.environ, "CI": "1"}, capture_output=True, text=True, timeout=240)
    (d / "check_after.log").write_text(chk.stdout + chk.stderr)
    mp4s = sorted(cwd.rglob("*.mp4"), key=lambda p: p.stat().st_mtime)
    out = {"r1_values_in_html": vals, "r1_labels_in_html": labels, "r1_title": bool(re.search(r"cost per (?:million )?(?:1m )?context tokens?", html, re.I)),
           "r1_fonts_below_40px": sum(1 for f in sorted(set(fonts)) if f < 40), "r1_min_font_px": min(fonts) if fonts else None, "r1_highlight_styling": bool(re.search(r"highlight|accent|peak|hot|hero|spike|highest", html, re.I)), "r1_check_pass": chk.returncode == 0, "r1_mp4": bool(mp4s),
           "r1_wh_dur": None, "r1_nonblank_last": None, "r1_html_lines": len(html.splitlines())}
    if mp4s:
        p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height,duration", "-of", "csv=p=0", str(mp4s[-1])], capture_output=True, text=True).stdout.split()
        out["r1_wh_dur"] = p[0] if p else None
        png = d / "last_frame.png"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "5.5", "-i", str(mp4s[-1]), "-frames:v", "1", str(png)])
        try:
            from PIL import Image
            im = Image.open(png).convert("RGB").resize((192, 108))
            px = list(im.getdata())
            bg = (8, 9, 12)
            out["r1_nonblank_last"] = round(sum(1 for c in px if sum(abs(a - b) for a, b in zip(c, bg)) > 40) / len(px), 3)
        except Exception as e:  # noqa: BLE001
            out["r1_nonblank_last"] = f"err {e}"
    return out


def norm(x: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", x.lower()).strip()


def truth_t5() -> dict[str, tuple[str, str]]:
    out = {}
    for f in sorted(FIX.glob("scripts/*/script.md")):
        lines = f.read_text().split("\n")
        title = next((l[2:].strip() for l in lines if l.startswith("# ")), "")
        st = next((l for l in lines[:40] if re.match(r"^[*_> ]*status[*_]*\s*:", l, re.I)), None)
        out[f.parent.name] = (title, re.sub(r"^[*_> ]*status[*_]*\s*:[*_ ]*", "", st, flags=re.I).strip() if st else "none")
    return out


T6_MUST = {"e31_opus_cost": r"2\.28", "e31_sonnet_cost": r"0\.45", "e34_h45_broke": r"3/3|3 of 3|three of three|all three", "e34_h55_clean": r"0/6|0/12|0 of 12|0 of 6|no .{0,20}(break|fail)",
           "e35_100k": r"100K", "e35_autocompact": r"autocompact|auto-compact", "e36_efficiency": r"efficien", "e36_ponytail": r"ponytail"}

HIDDEN = '''import sys
sys.path.insert(0, ".")
import pytest
from solution import slugify

LONG = "-".join(["abcdefghi"] * 10)

@pytest.mark.parametrize("src,want", [
    ("Hello, World!", "hello-world"),
    ("  Multiple   Spaces  ", "multiple-spaces"),
    ("Already-hyphenated", "already-hyphenated"),
    ("Caf\\u00e9 M\\u00fcnster", "caf-m-nster"),
    ("!!!", "untitled"),
    ("", "untitled"),
    ("x" * 70, "x" * 60),
    (LONG, LONG[:59]),
    ("Rock & Roll 101", "rock-roll-101"),
    ("--a--b--", "a-b"),
    ("UPPER_case_123", "upper-case-123"),
    ("tab\\tand\\nnewline", "tab-and-newline"),
])
def test_case(src, want):
    assert slugify(src) == want
'''


def rescore() -> None:
    """Recompute score fields for every run from its saved report (scorer fixes never touch the runs)."""
    rows = [json.loads(l) for l in open(OUT / "results.jsonl")]
    for r in rows:
        d = OUT / "runs" / f"{r['task']}_{r['cond']}"
        for k in [k for k in r if k.startswith(("t1_", "t2_", "t3_", "t4_"))]:
            del r[k]
        r.update(score(r["task"], d, (d / "report.txt").read_text(), d / "work" if r["task"] in ("T4", "R1") else FIX))
        if r.get("model") == briefs.HAIKU and (d / "subagent.jsonl").exists():
            n = norm_cost(str(d / "subagent.jsonl"))
            r["norm_cost"], r["turns_over_100k"] = n["norm_cost"], n["turns_over_100k"]
    (OUT / "results.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fixture()
    big()
    if sys.argv[1:] == ["rescore"]:
        return rescore()
    todo = briefs.plan() if sys.argv[1:] == ["all"] else briefs.plan_round2a() if sys.argv[1:] == ["round2a"] else briefs.plan_round2b() if sys.argv[1:] == ["round2b"] else briefs.plan_round3() if sys.argv[1:] == ["round3"] else [tuple(a.split(":")) for a in sys.argv[1:]]
    for task, cond in todo:
        if (OUT / "runs" / f"{task}_{cond}").exists():
            print("skip", task, cond); continue
        spent = sum(json.loads(l).get("total_cost") or 0 for l in open(OUT / "results.jsonl")) if (OUT / "results.jsonl").exists() else 0
        if spent >= BUDGET:
            raise SystemExit(f"budget cap reached: ${spent:.2f}")
        row = run_one(task, cond)
        print(json.dumps({k: row[k] for k in row if k in ("task", "cond", "sub_cost", "total_cost", "tr_turns", "tr_peak_ctx", "week") or k.startswith(("t1_", "t2_", "t3_", "t4_"))}), flush=True)
        if WEEK_STOP and (row.get("week") or 0) >= WEEK_STOP:
            raise SystemExit(f"weekly meter {row['week']}% >= {WEEK_STOP}%")


if __name__ == "__main__":
    main()
