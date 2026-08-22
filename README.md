# RUNLOG — code from the videos

Source code for [RUNLOG](https://github.com/runlog-tech) (@runlog), organized one folder per video.

## Videos

- [`01-mcp-server-in-20-minutes/`](01-mcp-server-in-20-minutes/) — "Build Your First MCP Server in 20 Minutes." A real MCP server (`project-memory`) with two tools that read and write a repo's own `memory/` markdown files.
- [`02-mcp-goes-stateless/`](02-mcp-goes-stateless/) — "Your MCP Server Just Got Demoted." `protocol_diff.py`, live proof that the legacy `initialize()` handshake every current MCP client calls is capped at last year's protocol version, while `discover()` reaches the new stateless spec.
- [`04-rebuild-your-claude-md/`](04-rebuild-your-claude-md/) — "Rebuild Your CLAUDE.md, Don't Accrete It." `/triage-memory` and `/audit-claude-md`, the two guardrail commands that stop a `CLAUDE.md` from turning into a changelog and catch it if it does anyway.
