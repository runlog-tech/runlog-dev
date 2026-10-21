"""Locked briefs and agent definitions for round 1 (PLAN.md). Do not edit after the first run."""
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parent.parent

L0 = {
    "T1": "Find every mention of meter.jsonl in the Python files under scripts/ and list them.",
    "T2": "Summarize scripts/autocompact-window-test/RESULTS.md.",
    "T3": "For every scripts/*/upload-notes.md, check whether it has a Primary title line and a Tags heading, and tell me which ones fail.",
    "T5": "For every scripts/*/script.md, report its title and its status line.",
    "T6": "Summarize entries 31, 34, 35 and 36 of notes/video_ideas.md.",
    "R1": "In this HyperFrames project, replace the placeholder scene in index.html with an animated horizontal bar chart of the cost per million context tokens for four context sizes: 0 to 50K $0.051, 50 to 100K $0.068, 100 to 150K $0.197, 150 to 250K $0.153. Make it look good and keep the 6 second duration. Run the check until it passes, then render it to an mp4.",
    "T4": "Write a Python function slugify(title) in solution.py with pytest tests in test_solution.py. Lowercase, ASCII letters and digits only, everything else becomes a single hyphen, no leading or trailing hyphens, at most 60 characters (cut at a hyphen boundary when possible), empty result becomes 'untitled'.",
}

L3 = {
    "T1": "Task: list every mention of the string `meter.jsonl` in Python files (`*.py`) under `scripts/` (recursive). Scope: only `scripts/**/*.py`; ignore other file types and anything outside `scripts/`. Method: one Grep with line numbers; do not open files unless a line is ambiguous. Stop when the Grep result is complete. Return format: one line per mention, `path:line`, nothing else, then a final line `total: N`.",
    "T2": "Task: summarize `scripts/autocompact-window-test/RESULTS.md` for a reader deciding whether to lower Claude Code's autocompact window. Read the file once in full. Return at most 8 bullets, each one sentence, each carrying its number or limit exactly as written in the file; no outside knowledge; finish with one line on what was NOT tested.",
    "T3": "Task: for each file matching `scripts/*/upload-notes.md` (one folder level deep) report (a) whether it has a line containing the word `Primary` followed by a title in backticks, and (b) whether it has a heading line exactly `## Tags`. Method: Glob the files, then one Grep per check across them (files-with-matches mode); do not read files in full. Return format: one line per folder, `folder: primary=yes|no tags=yes|no`, sorted by folder, then `failing: N`.",
    "T5": "Task: for each file matching `scripts/*/script.md` (one folder level deep) report (a) its title: the first line starting with `# `, without the `# `, and (b) its status: the first line within the first 40 lines that starts with `Status:` (ignore leading `**`, `>`, `_` and spaces; case-insensitive), first 60 characters after the colon, or `none` if there is no such line. Method: one Grep for the title lines and one Grep for the status lines across the files, first match per file (`-m 1`); do not read files in full. Return format: one line per folder, `folder | title | status`, sorted by folder, then `total: N`.",
    "T6": "Task: summarize entries 31, 34, 35 and 36 of `notes/video_ideas.md` (the entries are `## 31.` through `## 36.` headings; the file is large). Method: Grep the `## ` heading lines to find the line numbers of those entries, then Read only those line ranges (offset and limit); do not read the whole file. Return at most 10 bullets, each one sentence with its numbers exactly as written; finish with one line naming the entry that has the least detail.",
    "R1": "Task: edit `index.html` in the current directory (a HyperFrames project, 1920x1080, 30 fps) so the 6 second scene (keep `data-duration=\"6\"`) shows a horizontal bar chart. Title `COST PER CONTEXT TOKEN` (at least 64px). Four rows, each a label, a bar and the value at the bar end, in this order: `0 to 50K` `$0.051`, `50 to 100K` `$0.068`, `100 to 150K` `$0.197`, `150 to 250K` `$0.153`. Bar lengths proportional to the values. The `100 to 150K` bar in a different accent color from the others. Bars grow in one after another from the left with a GSAP stagger, registered on `window.__timelines[\"main\"]`. All text at least 40px, nothing outside the canvas, no gray text on the dark background. Method: write the file once, run `npm run check` and fix only what it reports, then render with `flock /tmp/hf-render.lock npm exec --yes -- hyperframes@0.8.82 render -w 4 --browser-gpu -o renders/out.mp4`. Stop when the render command exits 0 and `renders/out.mp4` exists. Return format: `check: pass|fail`, `render: ok|failed`, and the file name, nothing else.",
    "T4": "Task: create `solution.py` with `slugify(title: str) -> str` and `test_solution.py` (pytest) in the current directory. Spec: lowercase; keep only ASCII letters and digits; every run of other characters becomes one hyphen; strip leading and trailing hyphens; at most 60 characters, cutting at the last hyphen boundary at or before 60 when one exists; if the result is empty return `untitled`. Run `python -m pytest -q` once before finishing. Return format: the two file names, then the pytest summary line, nothing else.",
}

BASE_PROMPT = "You are a worker subagent. Do the task you are given and report back."
CONCISE = " Be extremely concise. Sacrifice grammar for the sake of concision. Final answer first, no preamble, no recap."
NARROW = {"R1": "Read, Write, Edit, Bash, Glob", "T1": "Read, Grep, Glob", "T2": "Read, Grep, Glob", "T3": "Read, Grep, Glob", "T5": "Read, Grep, Glob", "T6": "Read, Grep, Glob", "T4": "Read, Write, Edit, Bash"}
HAIKU, SONNET = "claude-haiku-5-5", "claude-sonnet-5-5"


def background() -> str:
    parts = [(REPO / "CLAUDE.md").read_text(), (REPO / "docs/VOCABULARY_AND_TONE_RULES.md").read_text()]
    return "\n\nProject background (for context):\n\n" + "\n\n".join(parts)


def condition(cond: str, task: str) -> dict:
    """Return {'brief','prompt','tools','model','effort'} for a condition id and task."""
    import re
    cond = re.sub(r"_r\d+$", "", cond)  # `_r2`, `_r3`: repeat runs of the same condition (Amendment 4)
    d = {"brief": L0[task], "prompt": BASE_PROMPT, "tools": None, "model": HAIKU, "effort": "high"}
    if cond.startswith("E_"):  # Amendment 2, part A: effort levels on the baseline brief
        d["effort"] = cond[2:]
    if cond.startswith("B_"):  # Amendment 3, part B: levers at High on the render task (baseline: E_high)
        k = cond[2:]
        if k in ("narrow", "combo"):
            d["tools"] = NARROW[task]
        if k in ("brief", "combo"):
            d["brief"] = L3[task]
        if k == "ponytail":
            d["prompt"] += "\n\n" + (HERE / "ponytail_instructions.txt").read_text()
        if k in ("karpathy", "combo"):
            d["prompt"] += "\n\n" + (HERE / "karpathy_claude_md.txt").read_text()
    if cond in ("L1", "L5"):
        d["prompt"] += CONCISE
    if cond in ("L2", "L5"):
        d["tools"] = NARROW[task]
    if cond in ("L3", "L5", "L7"):
        d["brief"] = L3[task]
    if cond == "L4":
        d["effort"] = "medium"
    if cond == "L6":
        d["prompt"] += "\n\n" + (HERE / "ponytail_instructions.txt").read_text()
    if cond == "L7":
        d["brief"] += background()
    if cond == "REF":
        d["model"], d["effort"] = SONNET, "medium"
    return d


def plan() -> list[tuple[str, str]]:
    """Amendment 1 order: the long-context tasks first, then the rest of the original plan (runner skips runs that exist)."""
    runs = [(t, c) for t in ("T5", "T6") for c in ("L0", "L1", "L2", "L3", "L4", "L5", "L7")] + [("T5", "REF"), ("T6", "REF")]
    runs += [(t, c) for t in ("T1", "T2", "T3") for c in ("L0", "L1", "L2", "L3", "L4", "L5", "L7")]
    runs += [("T4", c) for c in ("L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7")]
    runs += [(t, "REF") for t in ("T1", "T2", "T3", "T4")]
    return runs


def plan_round2a() -> list[tuple[str, str]]:
    return [("R1", "E_high"), ("R1", "E_xhigh"), ("R1", "E_max")]


def plan_round2b() -> list[tuple[str, str]]:
    return [("R1", c) for c in ("B_narrow", "B_brief", "B_ponytail", "B_karpathy", "B_combo")]


def plan_round3() -> list[tuple[str, str]]:
    return [("R1", f"{c}_r{n}") for n in (2, 3) for c in ("E_high", "B_brief", "B_combo")]
