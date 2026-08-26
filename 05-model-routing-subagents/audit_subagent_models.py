#!/usr/bin/env python3
"""Reports which model each subagent in a Claude Code session actually ran
on, versus the model: frontmatter its .claude/agents/<type>.md pins it to.

Real files this reads (verified against this project's own session data,
video_ideas.md entry 9, 2026-08-25):
  ~/.claude/projects/<project-slug>/<session-id>/subagents/agent-<id>.jsonl
  ~/.claude/projects/<project-slug>/<session-id>/subagents/agent-<id>.meta.json

.meta.json carries agentType (e.g. "firewall-auditor"). Each .jsonl line is
one transcript event; assistant turns carry the real model field, e.g.
"claude-haiku-4-5-20251001" -- this is ground truth for what actually ran,
independent of what the agent's model: frontmatter requested.

Usage (run from your repo's root, same directory as its .claude/agents/):
  python3 audit_subagent_models.py [session_id]
      No args: audits the most recently modified session with subagent data.
  python3 audit_subagent_models.py --all
      Aggregates every subagent run across every session in this project,
      tallied per subagent type -- the roll-up used for the "N/N routed
      correctly" check.
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path.cwd()
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"


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
                if model:
                    models_seen.add(model)

        actual_tiers = {tier_from_model_string(m) for m in models_seen}
        expected = declared.get(agent_type, "(no agent file)")
        mismatch = expected not in actual_tiers and expected != "(no agent file)"
        rows.append((agent_type, agent_id, expected, sorted(actual_tiers), mismatch))
    return rows


def print_rows(rows: list[tuple]) -> None:
    print(f"{'SUBAGENT':<20} {'PINNED':<10} {'ACTUALLY RAN':<20} STATUS")
    print("-" * 65)
    mismatches = 0
    for agent_type, agent_id, expected, actual_tiers, mismatch in rows:
        status = "MISMATCH" if mismatch else "ok"
        if mismatch:
            mismatches += 1
        print(f"{agent_type:<20} {expected:<10} {','.join(actual_tiers):<20} {status}")
    print()
    print(f"{len(rows)} subagent run(s), {mismatches} mismatch(es)")


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
