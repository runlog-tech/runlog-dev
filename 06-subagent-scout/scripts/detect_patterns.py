#!/usr/bin/env python3
"""Mechanical detector for subagent-scout.

Scans a project's real Claude Code session history (the main-thread
`*.jsonl` transcripts under `~/.claude/projects/<encoded-path>/`, NOT the
per-session `subagents/` subfolders -- this looks for work still running
inline that hasn't been delegated yet) for repeated tool-call sequences.

Real code doing the detection, not an LLM guessing from vibes: this is
the "receipts" half of subagent-scout. The judgment half (does this
pattern actually deserve a subagent, and what model tier) is left to the
calling Claude session, using the 4-question checklist from video 5.

Two signals are reported per candidate pattern, not one collapsed count:
  - cross_session_count: number of DISTINCT sessions the pattern recurs
    in -- evidence of a durable, recurring workflow.
  - max_single_session_count: the highest repeat count seen within any
    one session -- evidence that a single session's context got bloated
    by this loop, even if it never recurred elsewhere.

Both use the same minimum bar (default 3) but are surfaced separately,
since they support different claims and a real test run (RUNLOG's own
history) showed a pattern that was heavily single-session-only ("just
iterating," not a recurring habit) with zero cross-session recurrence.
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


def encode_project_path(repo_path: Path) -> str:
    # Matches Claude Code's own scheme: absolute path with "/" -> "-".
    return str(repo_path.resolve()).replace("/", "-")


def bash_shape(command: str) -> str:
    command = command.strip()
    m = re.match(r"^([a-zA-Z0-9_./-]+)", command)
    first = m.group(1) if m else command[:20]
    return f"Bash:{first.rsplit('/', 1)[-1]}"


def tool_shape(name: str, tool_input: dict) -> str:
    if name == "Bash":
        return bash_shape(tool_input.get("command", ""))
    if name in ("Read", "Edit", "Write"):
        path = tool_input.get("file_path", "")
        ext = path.rsplit(".", 1)[-1] if "." in path else "noext"
        return f"{name}:{ext}"
    if name == "Agent":
        return f"Agent:{tool_input.get('subagent_type', '?')}"
    return name


def extract_tool_sequence(jsonl_path: Path) -> list[str]:
    seq = []
    with jsonl_path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") != "assistant":
                continue
            content = entry.get("message", {}).get("content", [])
            if not isinstance(content, list):
                continue
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    seq.append(tool_shape(block.get("name", "?"), block.get("input") or {}))
    return seq


def find_ngrams(seq: list[str], sizes=(2, 3, 4)) -> Counter:
    counts = Counter()
    for n in sizes:
        for i in range(len(seq) - n + 1):
            counts[tuple(seq[i : i + n])] += 1
    return counts


def load_logged_signatures(repo_path: Path) -> set[str]:
    log_path = repo_path / ".claude" / "subagent-scout-log.md"
    if not log_path.exists():
        return set()
    signatures = set()
    for line in log_path.read_text().splitlines():
        m = re.match(r"^\|\s*`([^`]+)`\s*\|", line)
        if m:
            signatures.add(m.group(1))
    return signatures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-path", default=".", help="Project directory whose session history to scan")
    parser.add_argument("--min-count", type=int, default=3, help="Minimum occurrence bar (default 3)")
    parser.add_argument("--sizes", default="2,3,4", help="Comma-separated n-gram sizes to check")
    args = parser.parse_args()

    repo_path = Path(args.repo_path).resolve()
    sizes = tuple(int(x) for x in args.sizes.split(","))
    project_key = encode_project_path(repo_path)
    history_dir = Path.home() / ".claude" / "projects" / project_key

    if not history_dir.exists():
        print(json.dumps({"error": f"no session history found at {history_dir}"}), file=sys.stderr)
        sys.exit(1)

    jsonl_files = sorted(history_dir.glob("*.jsonl"))  # main-thread transcripts only, not */subagents/*
    per_session_seq = {f.name: extract_tool_sequence(f) for f in jsonl_files}

    cross_session_hits = defaultdict(set)  # gram -> {session_name, ...}
    max_single_session = defaultdict(int)  # gram -> highest count in any one session

    for session_name, seq in per_session_seq.items():
        grams = find_ngrams(seq, sizes)
        for gram, count in grams.items():
            if count >= 1:
                cross_session_hits[gram].add(session_name)
            max_single_session[gram] = max(max_single_session[gram], count)

    already_logged = load_logged_signatures(repo_path)

    candidates = []
    seen_supersets = set()
    for gram in sorted(set(cross_session_hits) | set(max_single_session), key=len, reverse=True):
        cross_count = len(cross_session_hits[gram])
        single_max = max_single_session[gram]
        if cross_count < args.min_count and single_max < args.min_count:
            continue
        signature = " -> ".join(gram)
        if signature in already_logged:
            continue
        # Skip grams that are fully contained in an already-emitted longer gram
        # (a 4-gram repeating implies its 3-gram/2-gram sub-patterns repeat too;
        # only surface the longest shape per cluster).
        if any(signature in longer for longer in seen_supersets):
            continue
        seen_supersets.add(signature)
        candidates.append(
            {
                "signature": signature,
                "length": len(gram),
                "cross_session_count": cross_count,
                "cross_session_names": sorted(cross_session_hits[gram]),
                "max_single_session_count": single_max,
            }
        )

    candidates.sort(key=lambda c: (c["cross_session_count"], c["max_single_session_count"]), reverse=True)

    print(
        json.dumps(
            {
                "repo_path": str(repo_path),
                "history_dir": str(history_dir),
                "sessions_scanned": len(jsonl_files),
                "min_count": args.min_count,
                "candidates": candidates,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
