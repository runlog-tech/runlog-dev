#!/usr/bin/env python3
"""
run_ablation.py - Tests whether DESIGN.md's Voice section specifically affects
em-dash compliance on b2b_saas, since Arm G (full doc) had 0 em-dashes there
while taste-skill alone (video 14) had 5. Runs arm_h_no_voice.json (same
brief, same taste-skill v2, DESIGN.md with the Voice section removed) against
the same local endpoint, same settings as run_benchmark.py.
"""

import os
import sys
import time
import json
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from render_real_tsx import extract_code, build_html  # noqa: E402

URL = "http://localhost:13305/api/v1/chat/completions"
MODEL = "Qwen3.6-27B-GGUF"
BASE = os.path.dirname(__file__)
OUT_DIR = BASE
PREVIEW_DIR = os.path.join(OUT_DIR, "html_preview")
os.makedirs(PREVIEW_DIR, exist_ok=True)


def run_one(prompt_file: str, run_id: str):
    with open(prompt_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    sys_p = data["system_prompt"]
    user_p = data["user_prompt"]

    print(f"\n=== RUNNING {run_id} (sys {data.get('tokens_system_est', 'N/A')} tok) ===")

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": user_p},
        ],
        "max_tokens": 15000,
        "stream": True,
    }

    t0 = time.time()
    first_token_time = None
    content_text = ""

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

    try:
        code = extract_code(content_text)
        html = build_html(code)
        with open(os.path.join(PREVIEW_DIR, f"{run_id}.html"), "w", encoding="utf-8") as f:
            f.write(html)
    except Exception as e:
        print(f"Preview failed: {e}")

    meta = {"run_id": run_id, "ttft_s": first_token_time, "total_time_s": total_time,
            "content_chars": len(content_text)}
    with open(os.path.join(OUT_DIR, f"{run_id}_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)


if __name__ == "__main__":
    # Usage: run_ablation.py <prompt_file.json> <run_id> [<prompt_file.json> <run_id> ...]
    # Runs each pair sequentially so multiple repeats can queue in one background task.
    args = sys.argv[1:]
    if not args:
        args = ["arm_h_no_voice.json", "b2b_saas__arm_h_no_voice_run1"]
    for i in range(0, len(args), 2):
        prompt_file, run_id = args[i], args[i + 1]
        run_one(os.path.join(BASE, prompt_file), run_id)
