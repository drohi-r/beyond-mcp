# MCP Config Examples

These examples show the cleanest ways to run `beyond-mcp` from common MCP clients.

## Claude Desktop

Local BEYOND on the same machine:

```json
{
  "mcpServers": {
    "beyond": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/beyond-mcp", "python", "-m", "beyond_mcp"],
      "env": {
        "BEYOND_HOST": "127.0.0.1",
        "BEYOND_OSC_PORT": "12000",
        "BEYOND_SAFETY_PROFILE": "show-safe"
      }
    }
  }
}
```

LAN or WireGuard target on another machine:

```json
{
  "mcpServers": {
    "beyond": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/beyond-mcp", "python", "-m", "beyond_mcp"],
      "env": {
        "BEYOND_HOST": "192.168.20.179",
        "BEYOND_OSC_PORT": "8000",
        "BEYOND_ALLOWED_HOSTS": "127.0.0.1,localhost,::1,192.168.20.179",
        "BEYOND_SAFETY_PROFILE": "show-safe"
      }
    }
  }
}
```

## Cursor / VS Code

```json
{
  "servers": {
    "beyond": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/beyond-mcp", "python", "-m", "beyond_mcp"],
      "env": {
        "BEYOND_HOST": "127.0.0.1",
        "BEYOND_OSC_PORT": "12000",
        "BEYOND_SAFETY_PROFILE": "show-safe"
      }
    }
  }
}
```

## Recommended Defaults

For a first real deployment:

- set `BEYOND_SAFETY_PROFILE=show-safe`
- keep `BEYOND_ALLOWED_HOSTS` explicit
- use LAN or WireGuard, not public internet
- validate with `display_popup`, `set_bpm`, and page/tab navigation first

## When To Use `read-only`

Use `BEYOND_SAFETY_PROFILE=read-only` when:

- you want visibility into config and reachability only
- you are testing network path before allowing writes
- you want to inspect previews or packet payloads without any live output changes
