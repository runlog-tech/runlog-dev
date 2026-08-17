"""Real receipts for RUNLOG video 2: connects to runlog-memory twice -- once the
way Claude Code does today (the legacy `initialize()` handshake, capped at
2025-11-25 by the SDK's own design), once via `discover()` (the only path to
the modern 2026-07-28 protocol) -- and prints what actually differs.

Not a demo script with invented output: every field printed here is read off
the real session/result objects from a live stdio connection to the actual
runlog-memory server (`main.py`, same server built in video 1).

Points at `sample-repo/` for the `list_pending_decisions` call -- a small
placeholder `memory/pending_decisions.md`, not the real RUNLOG project's own
planning data, so this folder runs standalone with nothing else to clone.
"""

import asyncio
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO = str(Path(__file__).resolve().parent / "sample-repo")
SERVER = StdioServerParameters(
    command="uv",
    args=["run", "--directory", str(Path(__file__).resolve().parent), "main.py"],
)


async def legacy_path():
    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            result = await session.initialize()
            call = await session.call_tool("list_pending_decisions", {"repo_path": REPO})
            return {
                "path": "initialize() -- what Claude Code does today",
                "negotiated_version": session.protocol_version,
                "server_reported_version": result.protocol_version,
                "result_meta": call.meta,
                "result_type": getattr(call, "result_type", None),
            }


async def modern_path():
    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            discover_result = await session.discover()
            call = await session.call_tool("list_pending_decisions", {"repo_path": REPO})
            return {
                "path": "discover() -- the only path to 2026-07-28",
                "negotiated_version": session.protocol_version,
                "server_supported_versions": discover_result.supported_versions,
                "result_meta": call.meta,
                "result_type": getattr(call, "result_type", None),
            }


async def main():
    legacy = await legacy_path()
    modern = await modern_path()

    for label, r in (("LEGACY (Claude Code, today)", legacy), ("MODERN (discover())", modern)):
        print(f"\n=== {label} ===")
        for k, v in r.items():
            print(f"  {k}: {v}")

    print("\n=== DIFF ===")
    print(f"  negotiated version: {legacy['negotiated_version']!r} -> {modern['negotiated_version']!r}")
    print(f"  tool result_type field present: {legacy['result_type'] is not None} -> {modern['result_type'] is not None}")


if __name__ == "__main__":
    asyncio.run(main())
