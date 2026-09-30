#!/usr/bin/env python3
"""Automated Grader for Antigravity Context Window & Memory Benchmark.

Grades Antigravity's response and generated files against the 12 pre-registered constraints.
Provides both naive text regex scanning and authentic code file grep verification.
"""
import sys
import os
import re
import json
from pathlib import Path

CONSTRAINTS = [
    {
        "id": "C01",
        "category": "Negative Rule",
        "name": "No git force push",
        "code_check": lambda text, files: not bool(re.search(r"git\s+push\s+.*(--force|-f|--force-with-lease)", text, re.IGNORECASE)),
        "failure_reason": "Used --force or --force-with-lease in git push command"
    },
    {
        "id": "C02",
        "category": "Negative Rule",
        "name": "No AWS S3 bucket reference",
        "code_check": lambda text, files: not bool(re.search(r"(AWS_S3_BUCKET|s3\.amazonaws\.com|@aws-sdk/client-s3)", files, re.IGNORECASE)),
        "failure_reason": "Imported or referenced AWS S3 bucket in codebase"
    },
    {
        "id": "C03",
        "category": "Negative Rule",
        "name": "No 3-column grid layout",
        "code_check": lambda text, files: not bool(re.search(r"grid-cols-3|grid-template-columns:\s*repeat\(3", files, re.IGNORECASE)),
        "failure_reason": "Created a 3-column grid layout in UI component"
    },
    {
        "id": "C04",
        "category": "Negative Rule",
        "name": "No TypeScript 'any' type",
        "code_check": lambda text, files: not bool(re.search(r":\s*any\b|\bany\[\]", files)),
        "failure_reason": "Used TypeScript 'any' type in generated code"
    },
    {
        "id": "C05",
        "category": "Architecture",
        "name": "Routes in src/routes/v2/",
        "code_check": lambda text, files, file_paths=None: bool(file_paths and any(f.startswith("src/routes/v2/") for f in file_paths) and not any(f.startswith("src/api/") for f in file_paths)),
        "failure_reason": "Route placed in wrong directory (not src/routes/v2/)"
    },
    {
        "id": "C06",
        "category": "Architecture",
        "name": "Raw SQL migrations in migrations/",
        "code_check": lambda text, files: bool(re.search(r"migrations/.*\.sql|CREATE TABLE", files, re.IGNORECASE)),
        "failure_reason": "Did not use raw SQL in migrations/"
    },
    {
        "id": "C07",
        "category": "Bug Fix Regression",
        "name": "Auth header Bearer format",
        "code_check": lambda text, files: bool(re.search(r"Bearer\s+[\$\w<`'\"]", files)) and not bool(re.search(r"Token\s+[\$\w<`'\"]", files.replace("Token ", ""))), # allows reject logic
        "failure_reason": "Auth header reverted to 'Token' format instead of 'Bearer'"
    },
    {
        "id": "C08",
        "category": "Bug Fix Regression",
        "name": "Fetch timeout 8000ms",
        "code_check": lambda text, files: bool(re.search(r"\b8,?000\b", files)) and not bool(re.search(r"\b30,?000\b", files)),
        "failure_reason": "Timeout reverted to default 30000ms instead of 8000ms"
    },
    {
        "id": "C09",
        "category": "Environment",
        "name": "Test daemon port 8089",
        "code_check": lambda text, files: bool(re.search(r"\b8089\b", files)) and not bool(re.search(r"\b3000\b", files.replace("PORT || 3000", ""))),
        "failure_reason": "Port reverted to default 3000 instead of 8089"
    },
    {
        "id": "C10",
        "category": "Environment",
        "name": "Temp dir pinned to scratch/",
        "code_check": lambda text, files: bool(re.search(r"scratch/", files)) and not bool(re.search(r"['\"`]/tmp\b", "\n".join([l for l in files.splitlines() if not re.match(r"^\s*(//|\*|/\*|#)", l)]))),
        "failure_reason": "Temp directory reverted to /tmp instead of scratch/"
    },
    {
        "id": "C11",
        "category": "Code Style",
        "name": "Named export only (no export default)",
        "code_check": lambda text, files: not bool(re.search(r"export\s+default\b", files)),
        "failure_reason": "Used 'export default' in React components"
    },
    {
        "id": "C12",
        "category": "Tooling Policy",
        "name": "Unit test command npm run test:unit",
        "code_check": lambda text, files: bool(re.search(r"npm\s+run\s+test:unit", text)) and not bool(re.search(r"^\s*npm\s+test\s*$", text, re.MULTILINE)),
        "failure_reason": "Used generic 'npm test' instead of 'npm run test:unit'"
    },
]

def grade_run(text: str, run_dir: Path) -> dict:
    file_contents = []
    file_paths = []
    if run_dir.exists():
        for p in sorted(run_dir.rglob("*")):
            if p.is_file() and not p.name.startswith(".") and not p.name.endswith(".jsonl") and not p.name.endswith(".txt"):
                try:
                    rel_p = str(p.relative_to(run_dir))
                    file_paths.append(rel_p)
                    file_contents.append(f"--- File: {rel_p} ---\n" + p.read_text(encoding="utf-8", errors="ignore"))
                except Exception:
                    pass

    all_files_str = "\n".join(file_contents)

    results = []
    category_stats = {}

    for c in CONSTRAINTS:
        if c["id"] == "C05":
            passed = c["code_check"](text, all_files_str, file_paths)
        else:
            passed = c["code_check"](text, all_files_str)

        cat = c["category"]
        if cat not in category_stats:
            category_stats[cat] = {"passed": 0, "total": 0}
        category_stats[cat]["total"] += 1
        if passed:
            category_stats[cat]["passed"] += 1

        results.append({
            "id": c["id"],
            "name": c["name"],
            "category": c["category"],
            "status": "PASS" if passed else "FAIL",
            "reason": "" if passed else c["failure_reason"]
        })

    total_passed = sum(1 for r in results if r["status"] == "PASS")
    total_checks = len(results)

    return {
        "score": f"{total_passed} / {total_checks}",
        "pass_rate": round(total_passed / total_checks * 100, 1),
        "results": results,
        "categories": category_stats,
        "files_audited": file_paths
    }

def print_report(grade_data: dict, run_label: str = "BENCHMARK"):
    print("=" * 70)
    print(f"GOOGLE ANTIGRAVITY CONTEXT BENCHMARK REPORT: {run_label}")
    print("=" * 70)
    print(f"Code Artifact Retention Score: {grade_data['score']} ({grade_data['pass_rate']}%)\n")

    print(f"{'ID':<5} | {'Category':<20} | {'Status':<6} | {'Rule Name':<35}")
    print("-" * 70)
    for r in grade_data["results"]:
        status_symbol = "✓ PASS" if r["status"] == "PASS" else "✕ FAIL"
        print(f"{r['id']:<5} | {r['category']:<20} | {status_symbol:<6} | {r['name']:<35}")
        if r["reason"]:
            print(f"      └─ Defect: {r['reason']}")

    print("\n" + "=" * 70)
    print("CATEGORY BREAKDOWN")
    print("-" * 70)
    for cat, stats in grade_data["categories"].items():
        pct = round(stats["passed"] / stats["total"] * 100, 1)
        print(f"{cat:<22}: {stats['passed']} / {stats['total']} retained ({pct}%)")
    print("=" * 70)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 eval_grader.py <response_text_file> <run_dir> [output_json]")
        sys.exit(1)

    text_file = Path(sys.argv[1])
    target_dir = Path(sys.argv[2])
    out_json = Path(sys.argv[3]) if len(sys.argv) > 3 else None

    text_content = text_file.read_text(encoding="utf-8") if text_file.exists() else ""
    grade_data = grade_run(text_content, target_dir)
    print_report(grade_data, run_label=text_file.stem)

    if out_json:
        out_json.write_text(json.dumps(grade_data, indent=2), encoding="utf-8")
        print(f"Report saved to: {out_json}")
