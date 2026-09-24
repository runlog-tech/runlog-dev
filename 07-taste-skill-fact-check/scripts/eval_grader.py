#!/usr/bin/env python3
"""
eval_grader.py - Automated compliance & defect grader for Taste Skill benchmarks.
Scans generated code against Section 9 ('AI Tells') of taste-skill v2.
"""

import os
import re
import sys
import json
from typing import Dict, Any, List

def grade_code(code: str) -> Dict[str, Any]:
    findings = []
    defects = 0

    # 1. Em-Dash Ban (§9.G)
    em_dashes = len(re.findall(r'—', code))
    if em_dashes > 0:
        findings.append({
            "rule": "no_em_dashes",
            "section": "§9.G",
            "severity": "FAIL",
            "count": em_dashes,
            "detail": f"Found {em_dashes} banned em-dashes ('—'). Rule requires hyphens ('-')."
        })
        defects += em_dashes

    # 2. Middle-Dot Rationing (§9.F)
    middle_dots = len(re.findall(r'·', code))
    multi_dot_lines = [line.strip() for line in code.splitlines() if line.count('·') > 1]
    if len(multi_dot_lines) > 0:
        findings.append({
            "rule": "no_middle_dot_spam",
            "section": "§9.F",
            "severity": "FAIL",
            "count": len(multi_dot_lines),
            "detail": f"Found {len(multi_dot_lines)} lines with >1 middle-dot ('·'). Max allowed is 1 per line."
        })
        defects += len(multi_dot_lines)

    # 3. Numbered Eyebrows Ban (§9.F)
    # Tightened 2026-09-23, second pass: \b00\d\b still matched SVG path data (icon `d`
    # attributes routinely contain "... 0 002-2v-6 ..." arc-flag digits) and bare data IDs
    # ("RAFT-001"). The skill's own banned examples ("00 / INDEX", "001 · Capabilities",
    # "06 · how it works") are always <=3 digits + a separator + the start of a word --
    # never a bare number. Matching that exact shape drops both false-positive classes
    # while still catching real eyebrow ornaments.
    numbered_eyebrows = re.findall(r'\b\d{1,3}\s*[/·]\s*[A-Za-z]', code)
    if numbered_eyebrows:
        findings.append({
            "rule": "no_numbered_eyebrows",
            "section": "§9.F",
            "severity": "FAIL",
            "count": len(numbered_eyebrows),
            "detail": f"Found numbered section eyebrows: {numbered_eyebrows[:3]}"
        })
        defects += len(numbered_eyebrows)

    # 4. Version Labels in Hero (§9.F)
    # Tightened 2026-09-23: BETA/ALPHA were case-insensitive and matched lowercase JS
    # identifiers (an `alpha` color-channel variable in rgba() template strings, not a
    # UI badge). Real badges in this house style render as literal uppercase text, so
    # those two now match case-sensitive; v\d+\.\d+ stays case-insensitive (real hits
    # confirmed: "v0.4.2" as visible JSX text).
    version_labels = re.findall(r'\bv\d+\.\d+\b', code, re.IGNORECASE) + \
        re.findall(r'\b(?:BETA|ALPHA|INVITE-ONLY|EARLY ACCESS)\b', code)
    if version_labels:
        findings.append({
            "rule": "no_version_labels",
            "section": "§9.F",
            "severity": "FAIL",
            "count": len(version_labels),
            "detail": f"Found banned hero version labels: {version_labels[:3]}"
        })
        defects += len(version_labels)

    # 5. 3-Column Equal Cards Ban (§9.C)
    three_col_matches = re.findall(r'\b(?:grid-cols-3|md:grid-cols-3|lg:grid-cols-3)\b', code)
    if three_col_matches:
        findings.append({
            "rule": "no_3_column_cards",
            "section": "§9.C",
            "severity": "FAIL",
            "count": len(three_col_matches),
            "detail": "Found 3-column equal grid layout. Rule strictly bans identical 3-card feature rows."
        })
        defects += len(three_col_matches)

    # 6. Pure Black Ban (§9.A)
    pure_black = re.findall(r'(?:#000000|#000\b|bg-black\b(?!/[0-9]))', code)
    if pure_black:
        findings.append({
            "rule": "no_pure_black",
            "section": "§9.A",
            "severity": "FAIL",
            "count": len(pure_black),
            "detail": f"Found {len(pure_black)} pure black references (#000000 / bg-black). Off-black/zinc-950 required."
        })
        defects += len(pure_black)

    # 7. Startup-Slop Copy (§9.D)
    buzzwords = re.findall(r'\b(?:seamless|seamlessly|elevate|elevates|revolutionize|unleash|next-gen|acme|john doe|sarah chan)\b', code, re.IGNORECASE)
    if buzzwords:
        findings.append({
            "rule": "no_buzzwords",
            "section": "§9.D",
            "severity": "FAIL",
            "count": len(buzzwords),
            "detail": f"Found banned AI startup buzzwords: {list(set(b.lower() for b in buzzwords))}"
        })
        defects += len(buzzwords)

    # 8. Div-Based Fake Terminal (§9.E / §9.F)
    fake_terminal_dots = re.findall(r'(?:rounded-full.*bg-red-|bg-red-500.*bg-yellow-|traffic-lights)', code, re.IGNORECASE)
    if fake_terminal_dots:
        findings.append({
            "rule": "no_fake_terminal",
            "section": "§9.E",
            "severity": "FAIL",
            "count": len(fake_terminal_dots),
            "detail": "Found div-based fake terminal mockup in hero. Rule bans div-simulated screenshots."
        })
        defects += len(fake_terminal_dots)

    # Motion Mechanics detection
    has_gsap = "gsap" in code.lower() or "scrolltrigger" in code.lower()
    has_framer = "framer-motion" in code.lower() or "motion." in code.lower()
    has_css_transition = "transition" in code.lower() or "duration-" in code.lower()

    motion_tech = []
    if has_gsap: motion_tech.append("GSAP")
    if has_framer: motion_tech.append("FramerMotion")
    if has_css_transition: motion_tech.append("CSSTransition")
    if not motion_tech: motion_tech.append("Static")

    return {
        "total_defects": defects,
        "is_clean": defects == 0,
        "findings": findings,
        "motion_tech": motion_tech,
        "raw_stats": {
            "lines": len(code.splitlines()),
            "chars": len(code),
            "em_dashes": em_dashes,
            "middle_dots": middle_dots
        }
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 eval_grader.py <path_to_code_file_or_dir>")
        sys.exit(1)

    target = sys.argv[1]
    files_to_grade = []
    if os.path.isdir(target):
        for root, _, files in os.walk(target):
            for f in files:
                if f.endswith(('.tsx', '.jsx', '.html', '.js', '.ts')):
                    files_to_grade.append(os.path.join(root, f))
    else:
        files_to_grade.append(target)

    results = {}
    print(f"\n=======================================================")
    print(f"   TASTE SKILL BENCHMARK: AUTOMATED DEFECT AUDIT       ")
    print(f"=======================================================\n")

    for fpath in files_to_grade:
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        res = grade_code(code)
        results[fpath] = res
        status = "PASSED (0 BANS VIOLATED)" if res["is_clean"] else f"FAILED ({res['total_defects']} BANS VIOLATED)"
        print(f"File: {os.path.basename(fpath)}")
        print(f"Status: {status} | Motion: {', '.join(res['motion_tech'])}")
        for finding in res["findings"]:
            print(f"  - [{finding['section']}] {finding['rule']}: {finding['detail']}")
        print("-------------------------------------------------------")

    report_path = os.path.join(os.path.dirname(target) if os.path.isfile(target) else target, "grader_report.json")
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nFull audit saved to {report_path}")
