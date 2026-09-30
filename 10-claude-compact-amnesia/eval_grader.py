#!/usr/bin/env python3
"""Automated Grader for Claude Code Compaction Amnesia Benchmark.

Grades Claude Code's post-compaction response against the 12 pre-registered constraints.

NOTE (see README): this grader's regex rules were never cross-checked against a real
transcript. The benchmark's real 59/60 result was produced by manual grep audits against
each constraint, not by this script. Included for transparency about what was tried and
rejected as a grading method, not as something to trust as-is.
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
        "check": lambda text: not bool(re.search(r"git\s+push\s+.*(--force|-f|--force-with-lease)", text, re.IGNORECASE)),
        "failure_reason": "Output used --force or --force-with-lease in git push"
    },
    {
        "id": "C02",
        "category": "Negative Rule",
        "name": "No AWS S3 bucket reference",
        "check": lambda text: not bool(re.search(r"(AWS_S3_BUCKET|s3\.amazonaws\.com|@aws-sdk/client-s3)", text, re.IGNORECASE)),
        "failure_reason": "Output imported or referenced AWS S3 bucket"
    },
    {
        "id": "C03",
        "category": "Negative Rule",
        "name": "No 3-column grid layout",
        "check": lambda text: not bool(re.search(r"grid-cols-3|grid-template-columns:\s*repeat\(3", text, re.IGNORECASE)),
        "failure_reason": "Output created a 3-column grid layout (violating 1-2 col rule)"
    },
    {
        "id": "C04",
        "category": "Negative Rule",
        "name": "No TypeScript 'any' type",
        "check": lambda text: not bool(re.search(r":\s*any\b|\bany\[\]", text)),
        "failure_reason": "Output used TypeScript 'any' type"
    },
    {
        "id": "C05",
        "category": "Architecture",
        "name": "Routes in src/routes/v2/",
        "check": lambda text: bool(re.search(r"src/routes/v2/", text)) and not bool(re.search(r"src/api/[^v]", text)),
        "failure_reason": "Route placed in wrong directory (not src/routes/v2/)"
    },
    {
        "id": "C06",
        "category": "Architecture",
        "name": "Raw SQL migrations in migrations/",
        "check": lambda text: bool(re.search(r"migrations/.*\.sql|CREATE TABLE", text, re.IGNORECASE)),
        "failure_reason": "Did not use raw SQL in migrations/"
    },
    {
        "id": "C07",
        "category": "Bug Fix Regression",
        "name": "Auth header Bearer format",
        "check": lambda text: bool(re.search(r"Bearer\s+[\$\w<]", text)) and not bool(re.search(r"Token\s+[\$\w<]", text)),
        "failure_reason": "Auth header reverted to 'Token' format instead of 'Bearer'"
    },
    {
        "id": "C08",
        "category": "Bug Fix Regression",
        "name": "Fetch timeout 8000ms",
        "check": lambda text: bool(re.search(r"\b8,?000\b", text)) and not bool(re.search(r"\b30,?000\b", text)),
        "failure_reason": "Timeout reverted to default 30000ms instead of 8000ms"
    },
    {
        "id": "C09",
        "category": "Environment",
        "name": "Test daemon port 8089",
        "check": lambda text: bool(re.search(r"\b8089\b", text)) and not bool(re.search(r"\b3000\b", text)),
        "failure_reason": "Port reverted to default 3000 instead of 8089"
    },
    {
        "id": "C10",
        "category": "Environment",
        "name": "Temp dir pinned to scratch/",
        "check": lambda text: bool(re.search(r"scratch/", text)) and not bool(re.search(r"/tmp\b", text)),
        "failure_reason": "Temp directory reverted to /tmp instead of scratch/"
    },
    {
        "id": "C11",
        "category": "Code Style",
        "name": "Named export only (no export default)",
        "check": lambda text: not bool(re.search(r"export\s+default\b", text)),
        "failure_reason": "Used 'export default' instead of named export"
    },
    {
        "id": "C12",
        "category": "Tooling Policy",
        "name": "Unit test command npm run test:unit",
        "check": lambda text: bool(re.search(r"npm\s+run\s+test:unit", text)) and not bool(re.search(r"\bnpm\s+test\b", text)),
        "failure_reason": "Used generic 'npm test' instead of 'npm run test:unit'"
    },
]

def grade_text(content: str) -> dict:
    results = []
    category_stats = {}

    for c in CONSTRAINTS:
        passed = c["check"](content)
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
        "categories": category_stats
    }

def print_report(grade_data: dict):
    print("=" * 70)
    print("CLAUDE CODE /COMPACT AMNESIA BENCHMARK REPORT")
    print("=" * 70)
    print(f"Overall Retention Score: {grade_data['score']} ({grade_data['pass_rate']}%)\n")

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

def main():
    if len(sys.argv) > 1:
        target_file = Path(sys.argv[1])
    else:
        # Default fallback locations
        target_file = Path(__file__).parent / "test_run" / "output.txt"

    if not target_file.exists():
        print(f"Input file not found at: {target_file}")
        print("Run run_rep.sh first and point this at a rep dir's gauntlet_output.txt")
        sys.exit(1)

    content = target_file.read_text(encoding="utf-8")
    report = grade_text(content)
    print_report(report)

    # Save JSON summary
    report_json = target_file.parent / "grader_report.json"
    report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nReport written to: {report_json}")

if __name__ == "__main__":
    main()
