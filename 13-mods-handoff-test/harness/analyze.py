"""Aggregates scaled-test runs: post-reset cost, context size, rule violations, constraint recall. Usage: python3 analyze.py"""

import json
import re
import statistics
from pathlib import Path

import grade
from run_pilot import total_cost

OUT = Path("/tmp/mods-pilot")


def rows(name):
    p = OUT / name / "meter.jsonl"
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def per_turn_costs(name):
    """Cost of each turn after the reset (ledger deltas; a fresh session restarts the ledger)."""
    r = rows(name)
    meta = json.loads((OUT / name / "meta.json").read_text())
    out, last = [], {}
    for i, x in enumerate(r):
        sid = x["session"]
        usd = (x.get("cost") or {}).get("usd", 0) or 0
        delta = usd - last.get(sid, 0)
        last[sid] = usd
        if i >= meta["reset_rows"]:
            out.append((round(delta, 4), x["context"].get("tokens")))
    return out


def run_summary(name):
    meta = json.loads((OUT / name / "meta.json").read_text())
    r = rows(name)
    pt = per_turn_costs(name)
    post = total_cost(r) - meta["reset_cost"]
    g = grade.grade(name)
    viol = {k: v for k, v in g["results"].items() if v["violations"] and k not in (13, 14)}
    f8 = g["results"].get(14, {"rule": "", "violations": ["no f8"]})
    return {"name": name, "reset_ctx": meta["reset_context"], "post_cost": post, "final_ctx": r[-1]["context"].get("tokens"),
            "turn_costs": [c for c, _ in pt], "violations": {k: len(v["violations"]) for k, v in viol.items()}, "recall": f8["rule"], "recall_missing": f8["violations"]}


if __name__ == "__main__":
    names = sorted(p.name for p in OUT.iterdir() if p.is_dir() and re.fullmatch(r"[A-D][1-9]", p.name) and (p / "new_files.json").exists())
    by = {}
    for n in names:
        s = run_summary(n)
        by.setdefault(n[0], []).append(s)
        print(f"{n}: reset_ctx={s['reset_ctx']} final_ctx={s['final_ctx']} post_cost=${s['post_cost']:.3f} violations={s['violations']} | {s['recall']} missing={s['recall_missing']}")
    print()
    for a, ss in sorted(by.items()):
        pc = [s["post_cost"] for s in ss]
        late = [statistics.mean(s["turn_costs"][-4:]) for s in ss]
        print(f"arm {a} (n={len(ss)}): post-reset cost mean ${statistics.mean(pc):.3f} (min {min(pc):.3f}, max {max(pc):.3f}); mean cost of last 4 follow-ups ${statistics.mean(late):.4f}; runs with any rule violation: {sum(1 for s in ss if s['violations'])}")
