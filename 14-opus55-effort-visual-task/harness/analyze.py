"""Per-run record from events.jsonl (stream-json): turns, tokens by type, tools, denials, cost, quota movement, outputs.
Usage: python3 analyze.py <run dir> [<run dir> ...]   writes <run dir>/record.json and prints a table.
"""

import collections
import json
import sys
from pathlib import Path


def record(d: Path) -> dict:
    ev = [json.loads(l) for l in (d / "events.jsonl").read_text().splitlines() if l.strip()]
    seen, turns = set(), []
    for e in ev:
        m = e.get("message") or {}
        if e["type"] == "assistant" and m.get("usage") and m.get("id") not in seen:
            seen.add(m["id"])
            u = m["usage"]
            tools = [b["name"] for b in m.get("content", []) if b.get("type") == "tool_use"]
            turns.append({"model": m.get("model"), "in": u.get("input_tokens", 0), "cache_write": u.get("cache_creation_input_tokens", 0),
                          "cache_read": u.get("cache_read_input_tokens", 0), "out": u.get("output_tokens", 0), "tools": tools})
    tot = collections.Counter()
    for t in turns:
        for k in ("in", "cache_write", "cache_read", "out"):
            tot[k] += t[k]
    tool_counts = collections.Counter(n for t in turns for n in t["tools"])
    res = next((e for e in reversed(ev) if e["type"] == "result"), {})
    rl = [e["rate_limit_info"].get("unifiedWindows", {}) for e in ev if e["type"] == "rate_limit_event"]
    f = lambda w, k: round(w[k]["utilization"] * 100) if k in w else None
    meta = json.loads((d / "meta.json").read_text())
    work = d / "work"
    outs = {p: (work / p).exists() for p in ("hyperframes/compositions/frames/04-result-one-the-bill.html", "hyperframes/compositions/frames/05-result-two-the-rules.html",
                                              "hyperframes/renders/04-result-one-the-bill.mp4", "hyperframes/renders/05-result-two-the-rules.mp4",
                                              "hyperframes/audio/04-result-one-the-bill.wav", "hyperframes/audio/05-result-two-the-rules.wav")}
    mu = res.get("modelUsage") or {}
    final = {k: sum(v.get(k2, 0) for v in mu.values()) for k, k2 in (("in", "inputTokens"), ("cache_write", "cacheCreationInputTokens"), ("cache_read", "cacheReadInputTokens"), ("out", "outputTokens"), ("thinking", "thinkingTokens"))}
    rec = {"final_tokens": final, "arm": meta["arm"], "model": meta["model"], "effort": meta["effort"], "assistant_turns": len(turns), "tokens": dict(tot),
           "tokens_total": sum(tot.values()), "output_share_pct": round(100 * tot["out"] / max(1, sum(tot.values())), 2),
           "peak_context": max((t["in"] + t["cache_write"] + t["cache_read"] for t in turns), default=0),
           "tool_calls": dict(tool_counts), "denied": sum(1 for e in ev if e.get("subtype") == "permission_denied"),
           "cost_usd": res.get("total_cost_usd"), "modelUsage": res.get("modelUsage"), "duration_s": round((res.get("duration_ms") or 0) / 1000),
           "num_turns_reported": res.get("num_turns"), "is_error": res.get("is_error"), "final_text": (res.get("result") or "")[:1500],
           "quota": {"5h_start": f(rl[0], "five_hour") if rl else None, "5h_end": f(rl[-1], "five_hour") if rl else None,
                     "week_start": f(rl[0], "seven_day") if rl else None, "week_end": f(rl[-1], "seven_day") if rl else None},
           "outputs": outs, "stopped_by_rule": json.loads((d / "summary.json").read_text()).get("stopped_by_rule") if (d / "summary.json").exists() else None}
    (d / "record.json").write_text(json.dumps(rec, indent=2))
    return rec


if __name__ == "__main__":
    for p in sys.argv[1:]:
        r = record(Path(p))
        print(f"{r['arm']} {r['model']} {r['effort']}: turns {r['assistant_turns']}, tokens {r['tokens']}, out share {r['output_share_pct']}%, cost ${r['cost_usd']}, "
              f"5h {r['quota']['5h_start']}->{r['quota']['5h_end']}, week {r['quota']['week_start']}->{r['quota']['week_end']}, denied {r['denied']}, tools {r['tool_calls']}, outputs {r['outputs']}")
