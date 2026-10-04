"""Shared video-19 protocol: workspace, prompts, scoring. Used by run_agy.py and run_claude.py."""
import json, random, re, string
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

N_SPEC = 16
WORDS = ("queue shard latency retry backoff ledger cursor snapshot replica quorum lease token "
         "schema index vacuum partition cache eviction checkpoint journal manifest pipeline "
         "gateway breaker throttle webhook payload digest cluster scheduler worker handler").split()

def _para(rng, n=5):
    out = []
    for _ in range(n):
        s = []
        for _ in range(rng.randint(3, 5)):
            w = [rng.choice(WORDS) for _ in range(rng.randint(10, 16))]
            s.append(" ".join(w).capitalize() + ".")
        out.append(" ".join(s))
    return "\n\n".join(out)

def make_workspace(ws: Path, seed: int, tool: str):
    rng = random.Random(seed)
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "docs").mkdir(exist_ok=True); (ws / "assets").mkdir(exist_ok=True); (ws / "src").mkdir(exist_ok=True)
    tok = "".join(rng.choices(string.ascii_uppercase + string.digits, k=4))
    vault = f"{rng.choice(['TANGERINE','LANTERN','GRANITE','HARBOR'])}-{rng.randint(1000,9999)}"
    ceiling = rng.randint(211, 989); pool = rng.randint(21, 97); paging = rng.randint(301, 899)
    secrets = {"hdr": f"// RUNLOG-HDR-{tok}", "vault": vault, "ceiling": ceiling, "pool": pool, "paging": paging}
    rules = (f"# Project rules\n\n- Every new TypeScript file must begin with the exact first line `{secrets['hdr']}`.\n"
             "- Keep answers short.\n")
    (ws / ("CLAUDE.md" if tool == "claude" else "AGENTS.md")).write_text(rules)
    img = Image.new("RGB", (1200, 260), (20, 24, 40)); d = ImageDraw.Draw(img)
    d.text((40, 40), "ACCESS NOTE", fill=(160, 170, 200), font=ImageFont.truetype("/usr/share/fonts/truetype/liberation2/LiberationMono-Bold.ttf", 40))
    d.text((40, 120), f"VAULT CODE: {vault}", fill=(255, 255, 255), font=ImageFont.truetype("/usr/share/fonts/truetype/liberation2/LiberationMono-Bold.ttf", 56))
    img.save(ws / "assets" / "vault.png")
    (ws / "docs" / "limits.json").write_text(json.dumps(
        {"service": "billing-gw", "REGION": "eu-west-2", "RETRY_CEILING": ceiling, "POOL_SIZE": pool, "LOG_LEVEL": "info"}, indent=2))
    for i in range(1, N_SPEC + 1):
        r = random.Random(seed * 100 + i)
        title3 = f"{r.choice(WORDS)}-{r.choice(WORDS)}-{r.randint(10,99)}"
        title12 = f"{r.choice(WORDS)}-{r.choice(WORDS)}-{r.randint(10,99)}"
        secs = [f"# Spec {i:02d}\n"]
        for s in range(1, 13):
            t = title3 if s == 3 else title12 if s == 12 else f"{r.choice(WORDS)} {r.choice(WORDS)} {r.randint(100,999)}"
            body = _para(r, 14)
            if i == 2 and s == 7:
                body += f"\n\nOperational note: the paging threshold is {paging} alerts per minute.\n"
            secs.append(f"## Section {s}: {t}\n\n{body}\n")
        (ws / "docs" / f"spec-{i:02d}.md").write_text("\n".join(secs))
        secrets[f"spec{i}_sec3"] = title3; secrets[f"spec{i}_sec12"] = title12
    (ws / ".truth.json").write_text(json.dumps(secrets))
    return secrets

NOFILES = " Use file tools only; do not run shell commands."
T1 = ("Setup for this session. Rule 1: never import the package `lodash` or `lodash-es`; and every exported "
      "function in this project must have a name starting with `rl_`. Also, look at the image assets/vault.png "
      "once, and read docs/limits.json once, so you know both. Reply with only the word 'ready'." + NOFILES)
FEATURES = [("src/auth.ts", "a function that checks a token string is non-empty"),
            ("src/upload.ts", "a function that returns whether a file size is under a limit"),
            ("src/billing.ts", "a function that totals an array of invoice amounts")]
def feature_turn(i):
    f, what = FEATURES[i]
    return f"Create {f} exporting {what}." + NOFILES
def filler_turn(i):
    return (f"Read docs/spec-{i:02d}.md in full, with no line limit. Reply with only the title of its LAST section, Section 12 (the text after 'Section 12:')." + NOFILES)
PROBES = [
 ("M3", "Earlier you looked at an image I pointed you to. What code did it show? Answer from memory; do not open any file or run any command."),
 ("M4", "What is our retry ceiling according to the project config you read earlier? Answer from memory; do not open any file or run any command."),
 ("M4B", "In that same config file, what was the connection pool size? Answer from memory; do not open any file or run any command."),
 ("M5", "List, in order, the three source files I first asked you to create in this session, by path. Answer from memory; do not open any file or run any command."),
 ("M6", "Earlier you read docs/spec-02.md. It contained an operational note about a paging threshold. What number was it? Answer from memory; do not open any file or run any command."),
 ("M1M2", "Create src/util/sum.ts exporting a function that totals an array of numbers. Use whatever array helper you like." + NOFILES),
]

def score(ws: Path, answers: dict, tool_steps: dict, truth: dict):
    s = {}
    s["M3"] = {"auto": truth["vault"] in answers["M3"], "reread": tool_steps.get("M3", 0) > 0}
    s["M4"] = {"auto": str(truth["ceiling"]) in answers["M4"], "reread": tool_steps.get("M4", 0) > 0}
    s["M4B"] = {"auto": str(truth["pool"]) in answers["M4B"], "reread": tool_steps.get("M4B", 0) > 0}
    s["M6"] = {"auto": str(truth["paging"]) in answers["M6"], "reread": tool_steps.get("M6", 0) > 0}
    a = answers["M5"]; idx = [a.find(p) for p in ("auth", "upload", "billing")]
    s["M5"] = {"auto": all(i >= 0 for i in idx) and idx == sorted(idx), "reread": tool_steps.get("M5", 0) > 0}
    p = ws / "src" / "util" / "sum.ts"; txt = p.read_text() if p.exists() else ""
    first = txt.splitlines()[0].strip() if txt else ""
    names = re.findall(r"export\s+(?:default\s+)?(?:async\s+)?(?:function|const|let)\s+(\w+)", txt)
    s["M1"] = {"auto": bool(txt) and "lodash" not in txt and bool(names) and all(n.startswith("rl_") for n in names), "file": bool(txt), "names": names, "lodash": "lodash" in txt}
    s["M2"] = {"auto": first == truth["hdr"], "first_line": first}
    base = {}
    for f, _ in FEATURES:
        q = ws / f; t = q.read_text() if q.exists() else ""
        base[f] = {"hdr": bool(t) and t.splitlines()[0].strip() == truth["hdr"],
                   "names_ok": all(n.startswith("rl_") for n in re.findall(r"export\s+(?:async\s+)?(?:function|const)\s+(\w+)", t)) and bool(t)}
    s["baseline_feature_files"] = base
    return s
