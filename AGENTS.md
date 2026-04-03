# AGENTS.md

## Project

- Product: `beyond-mcp`
- Domain: Pangolin BEYOND laser control
- Protocol: OSC
- Main entrypoint:
- `uv run python -m beyond_mcp.server`

## Core Rules

- Treat live laser control as high risk. Maintain explicit guardrails on write/destructive behavior.
- Keep protocol logic inside `src/beyond_mcp/`.
- Prefer additive fixes over sweeping rewrites.
- Add or update tests whenever behavior changes.

## Key Commands

```bash
uv sync
uv run python -m pytest -v
uv run python -m beyond_mcp.server
```

## Key Paths

- `src/beyond_mcp/server.py`: MCP server
- `src/beyond_mcp/`: OSC control logic and tools
- `tests/`: verification

## When Editing

- Preserve operator-safe defaults.
- Keep README claims consistent with the actual tool surface.
