#!/usr/bin/env python3
"""
run_benchmark.py - Runs Arms F (SYSTEM_DESIGN.md alone) and G (SYSTEM_DESIGN.md
+ taste-skill v2 combined) across the same 3 briefs used in video 14
(taste-skill-fact-check), against the same local Qwen3.6-27B-GGUF endpoint, so
results are directly comparable to that video's real naked/taste-skill/lean
directive numbers.
"""

import os
import sys
import time
import json
import requests

sys.path.insert(0, os.path.dirname(__file__))
from render_real_tsx import extract_code, build_html  # noqa: E402

URL = "http://localhost:13305/api/v1/chat/completions"
MODEL = "Qwen3.6-27B-GGUF"
BASE = os.path.dirname(__file__)
PROMPTS_DIR = os.path.join(BASE, "prompts")
OUT_DIR = os.path.join(BASE, "benchmark_results")
PREVIEW_DIR = os.path.join(OUT_DIR, "html_preview")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)

BRIEFS = ["b2b_saas", "portfolio", "interactive_widget"]
ARMS = ["arm_f_system_design", "arm_g_combined"]


def run_one(brief_id: str, arm_id: str):
    prompt_file = os.path.join(PROMPTS_DIR, brief_id, f"{arm_id}.json")
    with open(prompt_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    sys_p = data["system_prompt"]
    user_p = data["user_prompt"]
    run_id = f"{brief_id}__{arm_id}"

    print(f"\n=== RUNNING {run_id} (sys {data.get('tokens_system_est', 'N/A')} tok, real cl100k_base count) ===")

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": user_p},
        ],
        # 2026-09-24: bumped from video 14's 12000 baseline to 15000 -- splits the
        # difference with the 20000 truncation-retry cap that fixed 2/3 outliers
        # there, since Arm G's combined system prompt (SYSTEM_DESIGN.md + full
        # taste-skill v2) gives the model more to reconcile than either alone.
        "max_tokens": 15000,
        "stream": True,
    }

    t0 = time.time()
    first_token_time = None
    reasoning_text = ""
    content_text = ""

    try:
        r = requests.post(URL, json=payload, stream=True, timeout=1800)
        for line in r.iter_lines():
            if not line:
                continue
            dec = line.decode("utf-8")
            if dec.startswith("data: ") and dec.strip() != "data: [DONE]":
                try:
                    chunk = json.loads(dec[6:])
                    delta = chunk["choices"][0]["delta"]
                    if (delta.get("content") or delta.get("reasoning_content")) and first_token_time is None:
                        first_token_time = time.time() - t0
                        print(f"--> first token at {first_token_time:.2f}s")
                    if delta.get("reasoning_content"):
                        reasoning_text += delta["reasoning_content"]
                    if delta.get("content"):
                        content_text += delta["content"]
                        if len(content_text) % 400 < len(delta["content"]):
                            sys.stdout.write(".")
                            sys.stdout.flush()
                except Exception:
                    pass

        total_time = time.time() - t0
        print(f"\nDone {run_id} in {total_time:.1f}s ({len(content_text)} chars)")

        code_path = os.path.join(OUT_DIR, f"{run_id}.tsx")
        with open(code_path, "w", encoding="utf-8") as f:
            f.write(content_text)

        preview_path = os.path.join(PREVIEW_DIR, f"{run_id}.html")
        try:
            code = extract_code(content_text)
            html = build_html(code)
            with open(preview_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"Preview saved: {preview_path}")
        except Exception as e:
            print(f"Preview generation failed for {run_id}: {e}")

        meta = {
            "brief_id": brief_id,
            "arm_id": arm_id,
            "run_id": run_id,
            "ttft_s": first_token_time,
            "total_time_s": total_time,
            "reasoning_chars": len(reasoning_text),
            "content_chars": len(content_text),
            "content_lines": len(content_text.splitlines()),
            "code_path": code_path,
        }
        with open(os.path.join(OUT_DIR, f"{run_id}_meta.json"), "w") as f:
            json.dump(meta, f, indent=2)
        return meta

    except Exception as e:
        print(f"ERROR on {run_id}: {e}")
        return {"brief_id": brief_id, "arm_id": arm_id, "run_id": run_id, "error": str(e)}


if __name__ == "__main__":
    only = sys.argv[1:] if len(sys.argv) > 1 else None
    summary = []
    for brief_id in BRIEFS:
        for arm_id in ARMS:
            run_id = f"{brief_id}__{arm_id}"
            if only and not any(o in run_id for o in only):
                continue
            res = run_one(brief_id, arm_id)
            summary.append(res)

    with open(os.path.join(OUT_DIR, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print("\n\n=== GRILL-TASTE-SKILL BENCHMARK SUMMARY ===")
    for s in summary:
        if "error" in s:
            print(f"- {s['run_id']}: ERROR {s['error']}")
        else:
            print(f"- {s['run_id']}: TTFT={s['ttft_s']}s | Total={s['total_time_s']:.1f}s | Lines={s['content_lines']}")
