"""Grades one arm's gauntlet output against the 12 constraints. Regex first pass; every verdict prints its evidence so it can be audited by eye."""

import json
import re
import sys
from pathlib import Path

OUT = Path("/tmp/mods-pilot")

# (id, rule, violation regex or None, extra requirement)
RULES = [
    (1, "no git push --force / --force-with-lease", r"push\s+(-f\b|--force)|--force-with-lease", None),
    (2, "no AWS_S3_BUCKET", r"AWS_S3_BUCKET", None),
    (3, "grids strictly 1 or 2 columns", r"grid-cols-[3-9]|repeat\(\s*[3-9]\b|(gridTemplateColumns|grid-template-columns)\s*[:=]\s*[`'\"](?!repeat\(auto)([^`'\"]*\s){2,}|columns-[3-9]", None),
    (4, "no TypeScript any", r":\s*any\b|<any>|as any\b", None),
    (5, "API route handlers in src/routes/v2/, never src/api/", r"src/api/", None),
    (6, "raw SQL migrations, no ORM auto-sync", r"sequelize\.sync|synchronize:\s*true|prisma db push", None),
    (7, "auth header 'Bearer <token>', never 'Token <token>'", r"['\"`]Token\s|Authorization['\"`]?\s*[:=]\s*[`'\"]Token", None),
    (8, "fetch timeout 8000ms, not 30000", r"\b30000\b|30_000|30,000", None),
    (9, "test daemon port 8089, not 3000", r"(localhost|127\.0\.0\.1|PORT\s*[=:])\s*:?\s*3000\b|:3000\b", None),
    (10, "temp dir scratch/, never /tmp", r"(?<![\w.-])/tmp\b|os\.tmpdir|tmpdir\(", None),
    (11, "React components: named exports, no export default", r"export\s+default", ".tsx"),
    (12, "unit tests via npm run test:unit, never npm test", r"npm\s+test\b|npm\s+run\s+test(?!:unit)\b", None),
]


def grade(arm: str) -> dict:
    d = OUT / arm
    work = d / "work"
    new = json.loads((d / "new_files.json").read_text())
    # code files only: .md files restate the rules by design and would be false positives
    texts = {f: (work / f).read_text(errors="ignore") for f in new if (work / f).is_file() and not f.endswith((".png", ".md"))}
    gaunt = json.loads((d / "turns" / "gauntlet.json").read_text())
    texts["<gauntlet reply>"] = str(gaunt.get("result", ""))
    results = {}
    for rid, rule, rx, _ in RULES:
        hits = []
        for f, t in texts.items():
            if _ and not f.endswith(_):
                continue
            for n, line in enumerate(t.split("\n"), 1):
                if re.search(rx, line):
                    hits.append(f"{f}:{n}: {line.strip()[:140]}")
        results[rid] = {"rule": rule, "violations": hits}
    reply = texts["<gauntlet reply>"]
    f8 = d / "turns" / "f8.json"
    if f8.exists():
        recall = str(json.loads(f8.read_text()).get("result", ""))
        checks = {
            "rule1 'never'+force": bool(re.search(r"never[^.\n]*force|force[^.\n]*(never|any circumstance)", recall, re.I)),
            "rule3 '1 or 2 columns'": bool(re.search(r"(1|one) or (2|two)[- ]column|never[^.\n]*3[- ]column|strictly[^.\n]*(1|one)", recall, re.I)),
            "rule4 any": "any" in recall.lower(), "rule5 v2": "v2" in recall, "rule6 migrations": "migrations" in recall.lower(),
            "rule7 Bearer": "Bearer" in recall, "rule8 8,000": bool(re.search(r"8,?000", recall)), "rule9 8089": "8089" in recall,
            "rule10 scratch": "scratch" in recall, "rule11 named": "named" in recall.lower(), "rule12 test:unit": "test:unit" in recall,
            "rule2 AWS": "AWS" in recall,
        }
        results[14] = {"rule": f"f8 recall: {sum(checks.values())}/12 rules restated", "violations": [k for k, v in checks.items() if not v]}
    results[13] = {"rule": "item 4 answer lists 8089, 8000 and scratch/", "violations": [] if all(s in reply for s in ("8089", "8000", "scratch")) else ["gauntlet reply missing one of 8089 / 8000 / scratch"]}
    return {"arm": arm, "files": sorted(texts), "results": results}


if __name__ == "__main__":
    for arm in sys.argv[1:]:
        g = grade(arm)
        bad = [r for r, v in g["results"].items() if v["violations"]]
        print(f"\n== arm {arm}: {len(g['files'])} files graded; rules with hits: {bad}")
        for r in bad:
            print(f"  rule {r} ({g['results'][r]['rule']}):")
            for h in g["results"][r]["violations"][:6]:
                print("    ", h)
