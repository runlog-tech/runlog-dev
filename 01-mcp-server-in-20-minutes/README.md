# project-memory

MCP server from RUNLOG's debut video, "Build Your First MCP Server in 20 Minutes."

Two tools that read and write a repo's own `memory/` markdown files:

- `list_pending_decisions(repo_path)` — parses `memory/pending_decisions.md`'s table into structured data
- `log_experiment(repo_path, slug, branch, hypothesis, ...)` — appends a pre-registered row to `memory/experiments.md`

## Setup

```
uv init project-memory --no-workspace && cd project-memory
uv add "mcp[cli]"
```

Note: `uv init` creates the `project-memory/` folder but does not `cd` into it — the `&&` above is required, not optional. (Learned this the hard way when a viewer tried the earlier version of this sequence and hit `error: No pyproject.toml found`.)

Then copy `main.py` into that folder (or clone this repo directly).

## Register with Claude Code

```
claude mcp add runlog-memory -s project -- uv run --directory <path-to-this-folder> main.py
```

First use will prompt for approval in Claude Code — that's expected, not a bug. See the video for why.

## Requirements

The SDK used here (`mcp[cli]`) renamed `FastMCP` to `MCPServer` (now under `mcp.server.mcpserver`) at some point after most tutorials on this topic were published — if you're following an older guide and hit `ModuleNotFoundError: No module named 'mcp.server.fastmcp'`, that's why.
