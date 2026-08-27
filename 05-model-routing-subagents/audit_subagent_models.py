#!/usr/bin/env python3
"""Reports which model each subagent in a Claude Code session actually ran
on, versus the model: frontmatter its .claude/agents/<type>.md pins it to.

Real files this reads (verified against this project's own session data,
video_ideas.md entry 9, 2026-08-25):
  ~/.claude/projects/<project-slug>/<session-id>/subagents/agent-<id>.jsonl
  ~/.claude/projects/<project-slug>/<session-id>/subagents/agent-<id>.meta.json

.meta.json carries agentType (e.g. "firewall-auditor"). Each .jsonl line is
one transcript event; assistant turns carry a "model" field, e.g.
"claude-haiku-4-5-20251001" -- but this is only the DECLARED model, i.e.
whatever the harness logged for itself. GitHub issue #43869 (Claude Code,
still open as of 2026-08-27) showed the harness can log the wrong thing: the
declared field can disagree with the model that actually served the request.
The only ground truth is the model ID embedded in each thinking block's
server-generated, tamper-evident signature -- decoded here the same way
issue #43869's own author verified their fix attempt (comment by zadr007,
corrected version). A run with DECLARED=haiku but SERVED=opus is exactly the
silent-routing-failure this issue reports; a run with no signature at all
can't be verified either way (NO-SIGNATURE, absence of proof is not a pass).

Video 5's original claim ("6/6, not a bug") checked DECLARED only -- the
same field #43869 proved unreliable. This SERVED check is the retest.

Usage (run from your repo's root, same directory as its .claude/agents/):
  python3 audit_subagent_models.py [session_id]
      No args: audits the most recently modified session with subagent data.
  python3 audit_subagent_models.py --all
      Aggregates every subagent run across every session in this project,
      tallied per subagent type -- the roll-up used for the "N/N routed
      correctly" check.
"""

import base64
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path.cwd()
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"

FAMILIES = ("sonnet", "opus", "haiku", "fable")


def _family(model: str | None) -> str | None:
    if not model:
        return None
    text = model.lower()
    for name in FAMILIES:
        if name in text:
            return name
    return None  # unrecognised, incl. "inherit" -> nothing requested


def _served_from_signature(sig: str) -> set[str]:
    """Decodes the model ID out of a thinking block's response signature.
    Ported from issue #43869's own verification script (zadr007, corrected
    version) -- the model ID sits in the signature as a protobuf
    length-delimited string, so the byte before "claude-" is its length; the
    base64 also needs trying at 4 bit-offsets since the id isn't aligned."""
    out = set()
    for off in range(4):
        chunk = sig[off:]
        try:
            raw = base64.b64decode(chunk + "=" * (-len(chunk) % 4))
        except Exception:
            continue
        for m in re.finditer(rb"claude-", raw):
            i = m.start()
            if i and 3 <= raw[i - 1] <= 60:
                cand = raw[i:i + raw[i - 1]]
                if re.fullmatch(rb"claude-[a-z0-9\-]+", cand):
                    out.add(cand.decode())
    return out


def verify_signature(jsonl_path: Path, requested_tier: str) -> tuple[str, set[str], set[str]]:
    """Returns (verdict, declared_models, served_models) for one agent's
    transcript. verdict is one of:
      OK           declared and served agree, and served matches what was requested
      IGNORED      served never matches the requested tier -- the routing bug
      MISMATCH     declared disagrees with served (harness mislabelled its own log)
      NO-SIGNATURE no thinking-block signatures found -- can't verify either way
    IGNORED is checked before MISMATCH: a run can decl==served and still be
    IGNORED if both simply agree on the wrong (unrequested) model."""
    declared, served = set(), set()
    if jsonl_path.exists():
        for line in jsonl_path.read_text().splitlines():
            try:
                msg = json.loads(line).get("message") or {}
            except json.JSONDecodeError:
                continue
            if not isinstance(msg, dict):
                continue
            model = msg.get("model")
            if model and model.startswith("claude-"):
                declared.add(model)
            for block in msg.get("content") or []:
                if isinstance(block, dict) and block.get("signature"):
                    served |= _served_from_signature(block["signature"])

    if not served:
        return "NO-SIGNATURE", declared, served
    wanted = _family(requested_tier) if requested_tier != "(no agent file)" else None
    if wanted and wanted not in {_family(m) for m in served}:
        return "IGNORED", declared, served
    if declared != served:
        return "MISMATCH", declared, served
    return "OK", declared, served


def project_slug(repo_root: Path) -> str:
    return str(repo_root).replace("/", "-")


def declared_tiers(agents_dir: Path) -> dict[str, str]:
    tiers = {}
    for f in agents_dir.glob("*.md"):
        text = f.read_text()
        m = re.search(r"^model:\s*(\S+)", text, re.MULTILINE)
        tiers[f.stem] = m.group(1) if m else "(none)"
    return tiers


def tier_from_model_string(model: str) -> str:
    for tier in ("haiku", "sonnet", "opus"):
        if tier in model:
            return tier
    return model


def collect_rows(session_dir: Path, declared: dict[str, str]) -> list[tuple]:
    subagents_dir = session_dir / "subagents"
    if not subagents_dir.exists():
        return []

    rows = []
    for meta_path in sorted(subagents_dir.glob("agent-*.meta.json")):
        agent_id = meta_path.name.removesuffix(".meta.json").removeprefix("agent-")
        meta = json.loads(meta_path.read_text())

        # Agent Teams teammates (taskKind: in_process_teammate) get their model
        # from whoever spawned the team, not from a .claude/agents/*.md file --
        # a different routing mechanism this checklist doesn't govern. Excluded
        # here so they don't read as false "no agent file" mismatches.
        if meta.get("taskKind") == "in_process_teammate":
            continue

        agent_type = meta.get("agentType", "(unknown)")

        jsonl_path = subagents_dir / f"agent-{agent_id}.jsonl"
        models_seen = set()
        if jsonl_path.exists():
            for line in jsonl_path.read_text().splitlines():
                if '"model"' not in line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                model = event.get("message", {}).get("model")
                if model and model.startswith("claude-"):
                    models_seen.add(model)

        actual_tiers = {tier_from_model_string(m) for m in models_seen}
        expected = declared.get(agent_type, "(no agent file)")
        mismatch = expected not in actual_tiers and expected != "(no agent file)"
        verdict, declared_sigs, served_sigs = verify_signature(jsonl_path, expected)
        rows.append((agent_type, agent_id, expected, sorted(actual_tiers), mismatch,
                     verdict, sorted(served_sigs)))
    return rows


def print_rows(rows: list[tuple]) -> None:
    print(f"{'SUBAGENT':<20} {'PINNED':<10} {'DECLARED':<20} {'SERVED (signature)':<26} VERDICT")
    print("-" * 100)
    bad = 0
    for agent_type, agent_id, expected, actual_tiers, _mismatch, verdict, served in rows:
        if verdict in ("IGNORED", "MISMATCH"):
            bad += 1
        print(f"{agent_type:<20} {expected:<10} {','.join(actual_tiers):<20} "
              f"{','.join(served) or '(none)':<26} {verdict}")
    print()
    print(f"{len(rows)} subagent run(s), {bad} confirmed routing failure(s) (IGNORED/MISMATCH)")
    no_sig = sum(1 for r in rows if r[5] == "NO-SIGNATURE")
    if no_sig:
        print(f"{no_sig} run(s) had NO-SIGNATURE -- unverifiable, not counted as pass or fail")


def main():
    slug = project_slug(REPO_ROOT)
    projects_dir = Path.home() / ".claude" / "projects" / slug
    if not projects_dir.exists():
        print(f"no session data found at {projects_dir}")
        sys.exit(1)

    declared = declared_tiers(AGENTS_DIR)

    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        session_dirs = [p for p in projects_dir.iterdir() if p.is_dir() and (p / "subagents").exists()]
        rows = []
        for session_dir in sorted(session_dirs):
            rows.extend(collect_rows(session_dir, declared))
        if not rows:
            print("no sessions with subagent data found")
            sys.exit(1)
        print(f"aggregating {len(session_dirs)} session(s) with subagent runs")
        print_rows(rows)
        return

    if len(sys.argv) > 1:
        session_dir = projects_dir / sys.argv[1]
    else:
        session_dirs = [p for p in projects_dir.iterdir() if p.is_dir() and (p / "subagents").exists()]
        if not session_dirs:
            print("no sessions with subagent data found")
            sys.exit(1)
        session_dir = max(session_dirs, key=lambda p: p.stat().st_mtime)

    print(f"session: {session_dir.name}")
    rows = collect_rows(session_dir, declared)
    if not rows:
        print("no subagent runs found in this session")
        sys.exit(1)
    print_rows(rows)


if __name__ == "__main__":
    main()
