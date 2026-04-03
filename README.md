<p align="center">
  <img src="assets/banner.svg" alt="Beyond MCP" width="100%">
</p>

# Beyond MCP

<p align="center">
  <a href="https://github.com/drohi-r/beyond-mcp/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-orange?style=for-the-badge" alt="License"></a>
  <img src="https://img.shields.io/badge/Python-3.12%2B-blue?style=for-the-badge" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/MCP_Tools-44-F59E0B?style=for-the-badge" alt="44 MCP Tools">
  <img src="https://img.shields.io/badge/Categories-9-F59E0B?style=for-the-badge" alt="9 Categories">
  <img src="https://img.shields.io/badge/Tests-81-F59E0B?style=for-the-badge" alt="81 Tests">
</p>

An MCP server for [Pangolin BEYOND](https://pangolin.com/pages/beyond) laser software. Exposes 44 tools across 9 categories covering show control, cue management, zone configuration, live parameter control, and projector alignment — all via OSC.

Built for live production. Pairs with [MA2 Agent](https://github.com/drohi-r/grandma2-mcp), [Resolume MCP](https://github.com/drohi-r/resolume-mcp), and [Companion MCP](https://github.com/drohi-r/companion-mcp) for full AI-driven show control.

## Why this exists

Pangolin BEYOND is the industry-standard laser show software, but programming laser cues, adjusting zones, and tuning live parameters is entirely manual. An operator clicks through the BEYOND UI, one parameter at a time, across dozens of zones and cues.

This MCP server lets an AI assistant control BEYOND over OSC. It can trigger cues, adjust master brightness, mute zones, set BPM, control projector alignment, and manage live parameters — all from a single conversation. Combined with MA2 Agent, Resolume MCP, and Companion MCP, an AI assistant can orchestrate the entire show control stack.

## Quick start

```bash
git clone https://github.com/drohi-r/beyond-mcp && cd beyond-mcp
uv sync
uv run python -m beyond_mcp
```

Make sure BEYOND is running with OSC input enabled (configurable via `BEYOND_OSC_PORT`, defaults to 12000).

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `BEYOND_HOST` | `127.0.0.1` | BEYOND instance IP |
| `BEYOND_OSC_PORT` | `12000` | OSC receive port |
| `BEYOND_ALLOWED_HOSTS` | `127.0.0.1,localhost,::1` | Comma-separated allowlist for target hosts. Set `*` to allow any. |
| `BEYOND_READ_ONLY` | `0` | Set to `1` for read-only mode (blocks all write operations) |
| `BEYOND_TRANSPORT` | `stdio` | MCP transport (`stdio`, `sse`, `streamable-http`) |

## Tools

### System

| Tool | What it does |
|------|-------------|
| `get_server_config` | Return current MCP server configuration |
| `send_osc_raw` | Send a raw OSC message for any address not wrapped by a named tool |
| `preview_osc` | Preview an OSC message without sending it (dry-run inspection) |

### Master controls

| Tool | What it does |
|------|-------------|
| `set_master_brightness` | Set master brightness (0-100) |
| `blackout` | Activate blackout — disable all laser output |
| `enable_laser_output` | Enable laser output (undo blackout) |
| `disable_laser_output` | Disable laser output |
| `master_pause` | Pause or unpause master playback |
| `set_master_speed` | Set master playback speed |
| `stop_all_now` | Stop all playback immediately |
| `stop_all_sync` | Stop all playback with synchronization fade |

### BPM / Beat

| Tool | What it does |
|------|-------------|
| `set_bpm` | Set the BPM tempo value |
| `beat_tap` | Register a beat tap for tempo detection |
| `beat_resync` | Resynchronize beat timing |

### Cue mode

| Tool | What it does |
|------|-------------|
| `set_cue_mode_single` | Set cue mode to Single Cue (one active cue at a time) |
| `set_cue_mode_one_per` | Set cue mode to One Per (one per group) |
| `set_cue_mode_multi` | Set cue mode to Multi Cue (multiple simultaneous) |

### Cue / Cell control

| Tool | What it does |
|------|-------------|
| `select_cue` | Select a cue by page and cue index |
| `start_cue_by_name` | Start a cue by name |
| `stop_cue_by_name` | Stop a cue by name |
| `stop_cue_now` | Stop a specific cue immediately |
| `focus_cell` | Focus on a cell by page and cue coordinates |
| `start_cell` | Start the currently focused cell |
| `stop_cell` | Stop the currently focused cell |
| `unselect_all_cues` | Deselect all active cues |

### Page / Tab navigation

| Tool | What it does |
|------|-------------|
| `select_page` | Select a page by index |
| `select_next_page` | Navigate to the next page |
| `select_prev_page` | Navigate to the previous page |
| `select_tab` | Select a tab by index |
| `select_tab_by_name` | Select a tab by name |

### Zone control

| Tool | What it does |
|------|-------------|
| `mute_zone` | Mute a projection zone by index |
| `unmute_zone` | Unmute a projection zone by index |
| `unmute_all_zones` | Unmute all projection zones |
| `stop_zone` | Stop output on a zone with optional fade time |
| `select_zone` | Select a projection zone |
| `set_zone_brightness` | Set brightness for a specific zone (0-100) |

### Live control parameters

Master-scope parameters for size, position, rotation, color, zoom, and scan rate.

| Tool | What it does |
|------|-------------|
| `set_master_size` | Set master size X and Y |
| `set_master_position` | Set master position X and Y |
| `set_master_rotation` | Set master rotation angles X, Y, Z |
| `set_master_color` | Set master color RGB (0-255 each) |
| `set_master_zoom` | Set master zoom (0-100) |
| `set_master_scan_rate` | Set master scan rate (10-200) |

### Projector control

| Tool | What it does |
|------|-------------|
| `set_projector_size` | Set projector output size X and Y |
| `set_projector_position` | Set projector output position X and Y |

## Claude Desktop

```json
{
  "mcpServers": {
    "beyond": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/beyond-mcp", "python", "-m", "beyond_mcp"],
      "env": {
        "BEYOND_HOST": "127.0.0.1",
        "BEYOND_OSC_PORT": "12000"
      }
    }
  }
}
```

## VS Code / Cursor

```json
{
  "servers": {
    "beyond": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/beyond-mcp", "python", "-m", "beyond_mcp"],
      "env": {
        "BEYOND_HOST": "127.0.0.1",
        "BEYOND_OSC_PORT": "12000"
      }
    }
  }
}
```

## Production safety

This server is designed for live show environments where accidental commands can disrupt a running laser show.

- **UDP fire-and-forget** — BEYOND OSC control uses UDP, meaning commands are sent without acknowledgement. There is no rollback. Every tool call is a real action on the laser system.
- **Host allowlisting** — only `127.0.0.1`, `localhost`, and `::1` are permitted by default. Add LAN hosts explicitly via `BEYOND_ALLOWED_HOSTS`. Set `*` to allow any host.
- **Read-only mode** — set `BEYOND_READ_ONLY=1` to block all write operations. Only `get_server_config` and `preview_osc` remain available.
- **Preview before send** — `preview_osc` returns the exact OSC packet details (address, values, type tags, target) without transmitting anything. Use this to inspect what a command will do before committing.
- **Input validation** — all tools with documented parameter ranges enforce bounds before any OSC message is built. Brightness, zoom, scan rate, size, position, rotation, color, BPM, speed, and fade times are all range-checked. Invalid inputs return structured JSON errors, never raw exceptions.
- **Error isolation** — all tools are wrapped in `_handle_errors`. OSC send failures, JSON parse errors, validation failures, and unexpected exceptions return `{"ok": false, "error": "...", "blocked": true}` instead of crashing the MCP session.
- **Transport validation** — only `stdio`, `sse`, and `streamable-http` transports are accepted. Invalid transport values raise immediately at startup.
- **Port validation** — `BEYOND_OSC_PORT` is validated as an integer in the 1-65535 range at config load time.
- **Raw escape hatch** — `send_osc_raw` allows any OSC address for coverage beyond the named tools, but requires explicit JSON array input and validates structure before sending.

## Development

```bash
uv sync
uv run python -m pytest -v
```

## License

[Apache 2.0](LICENSE)
