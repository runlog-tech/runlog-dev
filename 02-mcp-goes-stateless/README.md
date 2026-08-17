# mcp-goes-stateless

The live proof from RUNLOG's "Your MCP Server Just Got Demoted" — MCP's
spec went stateless on 2026-07-28 (the `initialize`/`initialized` handshake
is gone), but the legacy handshake every current MCP client still calls,
including Claude Code, is hard-capped at `2025-11-25` by the SDK's own
design. Only `discover()` reaches the modern spec, and that's a client-side
decision the server can't control.

`protocol_diff.py` connects to `runlog-memory` (the same server built in
[video 1](../01-mcp-server-in-20-minutes/)) two different ways and prints
exactly what each one negotiates — not invented output, real session/result
objects from a live stdio connection.

## Run it

```
uv run python3 protocol_diff.py
```

Self-contained: `main.py` (the server) and `sample-repo/` (placeholder data
for the one tool call the script makes) are both included, so this folder
runs on its own without cloning `01-mcp-server-in-20-minutes/` too.

Expected output:

```
=== LEGACY (Claude Code, today) ===
  negotiated_version: 2025-11-25
  result_meta: None

=== MODERN (discover()) ===
  negotiated_version: 2026-07-28
  result_meta: {'io.modelcontextprotocol/serverInfo': {...}}

=== DIFF ===
  negotiated version: '2025-11-25' -> '2026-07-28'
```

## Why this matters

If your MCP server's SDK already supports the 2026-07-28 spec, that alone
doesn't mean your tools are actually speaking it — the negotiated version is
decided by which handshake your *client* calls, not by what your server is
capable of. See the video for the full breakdown, including whether
switching is worth it today.
