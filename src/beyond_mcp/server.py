"""
BEYOND MCP Server

MCP server for Pangolin BEYOND laser software — show control,
cue management, zone configuration, and live parameter control via OSC.

OSC addresses based on Pangolin wiki documentation:
https://wiki.pangolin.com/doku.php?id=beyond:osc_commands
"""

from __future__ import annotations

import json
import os
from functools import wraps
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import BeyondClient, build_osc_message
from .config import load_config


mcp = FastMCP(
    "BEYOND MCP",
    instructions=(
        "Control Pangolin BEYOND laser software via OSC. "
        "Use named tools for common operations. Use send_osc_raw for addresses "
        "not yet wrapped. All OSC addresses are from Pangolin documentation — "
        "validate against your installed BEYOND version."
    ),
)


def _client() -> BeyondClient:
    return BeyondClient(load_config())


def _json(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)


def _error(message: str, **extra: Any) -> str:
    return _json({"ok": False, "error": message, **extra})


def _handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except json.JSONDecodeError as exc:
            return _error(f"Invalid JSON input: {exc.msg}", blocked=True)
        except ValueError as exc:
            return _error(str(exc), blocked=True)
        except OSError as exc:
            return _error("OSC send failed.", detail=str(exc), blocked=False)
        except Exception as exc:
            return _error(f"Unexpected error: {type(exc).__name__}: {exc}", blocked=False)
    return wrapper


def _check_write() -> None:
    config = load_config()
    if config.read_only:
        raise ValueError(
            "Server is in read-only mode (BEYOND_READ_ONLY=1). "
            "Write operations are disabled."
        )


def _osc(address: str, values: list[Any]) -> dict[str, Any]:
    """Send OSC message and return result dict."""
    _check_write()
    return _client().send_osc(address, values)


def _validate_float_range(value: float, name: str, min_v: float, max_v: float) -> None:
    if not (min_v <= value <= max_v):
        raise ValueError(f"{name} must be between {min_v} and {max_v}, got {value}")


def _validate_int_choice(value: int, name: str, choices: set[int]) -> None:
    if value not in choices:
        raise ValueError(f"{name} must be one of {sorted(choices)}, got {value}")


def _validate_non_negative(value: float, name: str) -> None:
    if value < 0:
        raise ValueError(f"{name} must be >= 0, got {value}")


# ============================================================
# System
# ============================================================


@mcp.tool()
@_handle_errors
def get_server_config() -> str:
    """Return current BEYOND MCP server configuration and safety settings."""
    config = load_config()
    return _json({
        "host": config.host,
        "osc_port": config.osc_port,
        "target": config.target,
        "allowed_hosts": sorted(config.allowed_hosts),
        "read_only": config.read_only,
    })


@mcp.tool()
@_handle_errors
def send_osc_raw(address: str, values_json: str = "[]", type_tags: str = "") -> str:
    """Send a raw OSC message to BEYOND. Use for any address not wrapped by a named tool."""
    _check_write()
    values = json.loads(values_json)
    if not isinstance(values, list):
        raise ValueError("values_json must be a JSON array.")
    result = _client().send_osc(address, values, type_tags=type_tags or None)
    return _json(result)


@mcp.tool()
@_handle_errors
def preview_osc(address: str, values_json: str = "[]", type_tags: str = "") -> str:
    """Preview an OSC message without sending it. Returns the packet details for inspection."""
    values = json.loads(values_json)
    if not isinstance(values, list):
        raise ValueError("values_json must be a JSON array.")
    tags = type_tags or None
    packet = build_osc_message(address, values, type_tags=tags)
    config = load_config()
    return _json({
        "preview": True,
        "address": address,
        "values": values,
        "type_tags": type_tags or "auto",
        "target_host": config.host,
        "target_port": config.osc_port,
        "packet_bytes": len(packet),
        "note": "This is a preview only. No OSC message was sent.",
    })


# ============================================================
# Master Controls
# ============================================================


@mcp.tool()
@_handle_errors
def set_master_brightness(value: float) -> str:
    """Set master brightness (0-100)."""
    _validate_float_range(value, "brightness", 0, 100)
    return _json(_osc("/beyond/master/livecontrol/brightness", [value]))


@mcp.tool()
@_handle_errors
def blackout() -> str:
    """Activate blackout — disable all laser output."""
    return _json(_osc("/beyond/general/BlackOut", []))


@mcp.tool()
@_handle_errors
def enable_laser_output() -> str:
    """Enable laser output (undo blackout)."""
    return _json(_osc("/beyond/general/EnableLaserOutput", []))


@mcp.tool()
@_handle_errors
def disable_laser_output() -> str:
    """Disable laser output."""
    return _json(_osc("/beyond/general/DisableLaserOutput", []))


@mcp.tool()
@_handle_errors
def master_pause(enabled: int) -> str:
    """Pause or unpause master playback. 1=pause, 0=unpause."""
    _validate_int_choice(enabled, "enabled", {0, 1})
    return _json(_osc("/beyond/general/MasterPause", [enabled]))


@mcp.tool()
@_handle_errors
def set_master_speed(value: float) -> str:
    """Set master playback speed (0-10)."""
    _validate_float_range(value, "speed", 0, 10)
    return _json(_osc("/beyond/general/MasterSpeed", [value]))


@mcp.tool()
@_handle_errors
def stop_all_now() -> str:
    """Stop all playback immediately."""
    return _json(_osc("/beyond/general/StopAllNow", []))


@mcp.tool()
@_handle_errors
def stop_all_sync(fade_time: float = 0.0) -> str:
    """Stop all playback with synchronization fade."""
    _validate_non_negative(fade_time, "fade_time")
    return _json(_osc("/beyond/general/StopAllSync", [fade_time]))


# ============================================================
# BPM / Beat
# ============================================================


@mcp.tool()
@_handle_errors
def set_bpm(bpm: float) -> str:
    """Set the BPM tempo value (1-999)."""
    _validate_float_range(bpm, "bpm", 1, 999)
    return _json(_osc("/beyond/general/SetBpm", [bpm]))


@mcp.tool()
@_handle_errors
def beat_tap() -> str:
    """Register a beat tap for tempo detection."""
    return _json(_osc("/beyond/general/BeatTap", []))


@mcp.tool()
@_handle_errors
def beat_resync() -> str:
    """Resynchronize beat timing."""
    return _json(_osc("/beyond/general/BeatResync", []))


# ============================================================
# Cue Mode
# ============================================================


@mcp.tool()
@_handle_errors
def set_cue_mode_single() -> str:
    """Set cue mode to Single Cue (one active cue at a time)."""
    return _json(_osc("/beyond/general/OneCue", []))


@mcp.tool()
@_handle_errors
def set_cue_mode_one_per() -> str:
    """Set cue mode to One Per (one per group)."""
    return _json(_osc("/beyond/general/OnePer", []))


@mcp.tool()
@_handle_errors
def set_cue_mode_multi() -> str:
    """Set cue mode to Multi Cue (multiple simultaneous cues)."""
    return _json(_osc("/beyond/general/MultiCue", []))


# ============================================================
# Cue / Cell Control
# ============================================================


@mcp.tool()
@_handle_errors
def select_cue(page: int, cue: int) -> str:
    """Select a cue by page and cue index."""
    return _json(_osc("/beyond/general/SelectCue", [page, cue]))


@mcp.tool()
@_handle_errors
def start_cue_by_name(name: str) -> str:
    """Start a cue by name."""
    return _json(_osc("/beyond/general/StartCue", [name]))


@mcp.tool()
@_handle_errors
def stop_cue_by_name(name: str) -> str:
    """Stop a cue by name."""
    return _json(_osc("/beyond/general/StopCue", [name]))


@mcp.tool()
@_handle_errors
def stop_cue_now(page: int, cue: int) -> str:
    """Stop a specific cue immediately."""
    return _json(_osc("/beyond/general/StopCueNow", [page, cue]))


@mcp.tool()
@_handle_errors
def focus_cell(page: int, cue: int) -> str:
    """Focus on a cell by page and cue coordinates."""
    return _json(_osc("/beyond/general/FocusCell", [page, cue]))


@mcp.tool()
@_handle_errors
def start_cell() -> str:
    """Start the currently focused cell."""
    return _json(_osc("/beyond/general/StartCell", []))


@mcp.tool()
@_handle_errors
def stop_cell() -> str:
    """Stop the currently focused cell."""
    return _json(_osc("/beyond/general/StopCell", []))


@mcp.tool()
@_handle_errors
def unselect_all_cues() -> str:
    """Deselect all active cues."""
    return _json(_osc("/beyond/general/UnselectAllCue", []))


# ============================================================
# Page / Tab Navigation
# ============================================================


@mcp.tool()
@_handle_errors
def select_page(page_index: int) -> str:
    """Select a page by index."""
    return _json(_osc("/beyond/general/SelectPage", [page_index]))


@mcp.tool()
@_handle_errors
def select_next_page() -> str:
    """Navigate to the next page."""
    return _json(_osc("/beyond/general/SelectNextPage", []))


@mcp.tool()
@_handle_errors
def select_prev_page() -> str:
    """Navigate to the previous page."""
    return _json(_osc("/beyond/general/SelectPrevPage", []))


@mcp.tool()
@_handle_errors
def select_tab(tab_index: int) -> str:
    """Select a tab by index."""
    return _json(_osc("/beyond/general/SelectTab", [tab_index]))


@mcp.tool()
@_handle_errors
def select_tab_by_name(name: str) -> str:
    """Select a tab by name."""
    return _json(_osc("/beyond/general/SelectTabName", [name]))


# ============================================================
# Zone Control
# ============================================================


@mcp.tool()
@_handle_errors
def mute_zone(zone_index: int) -> str:
    """Mute a projection zone by index."""
    return _json(_osc("/beyond/general/MuteZone", [zone_index]))


@mcp.tool()
@_handle_errors
def unmute_zone(zone_index: int) -> str:
    """Unmute a projection zone by index."""
    return _json(_osc("/beyond/general/UnmuteZone", [zone_index]))


@mcp.tool()
@_handle_errors
def unmute_all_zones() -> str:
    """Unmute all projection zones."""
    return _json(_osc("/beyond/general/UnmuteAllZone", []))


@mcp.tool()
@_handle_errors
def stop_zone(zone_index: int, fade_time: float = 0.0) -> str:
    """Stop output on a zone with optional fade time."""
    _validate_non_negative(fade_time, "fade_time")
    return _json(_osc("/beyond/general/StopZone", [zone_index, fade_time]))


@mcp.tool()
@_handle_errors
def select_zone(zone_index: int) -> str:
    """Select a projection zone."""
    return _json(_osc("/beyond/general/SelectZone", [zone_index]))


@mcp.tool()
@_handle_errors
def set_zone_brightness(zone_index: int, value: float) -> str:
    """Set brightness for a specific zone (0-100)."""
    _validate_float_range(value, "brightness", 0, 100)
    return _json(_osc(f"/beyond/zone/{zone_index}/livecontrol/brightness", [value]))


# ============================================================
# Live Control Parameters (Master scope)
# ============================================================


@mcp.tool()
@_handle_errors
def set_master_size(x: float, y: float) -> str:
    """Set master size X and Y (-400 to 400)."""
    _validate_float_range(x, "size_x", -400, 400)
    _validate_float_range(y, "size_y", -400, 400)
    return _json(_osc("/beyond/master/livecontrol/size", [x, y]))


@mcp.tool()
@_handle_errors
def set_master_position(x: float, y: float) -> str:
    """Set master position X and Y (-32768 to 32768)."""
    _validate_float_range(x, "pos_x", -32768, 32768)
    _validate_float_range(y, "pos_y", -32768, 32768)
    return _json(_osc("/beyond/master/livecontrol/pos", [x, y]))


@mcp.tool()
@_handle_errors
def set_master_rotation(x: float, y: float, z: float) -> str:
    """Set master rotation angles X, Y, Z (-2880 to 2880)."""
    _validate_float_range(x, "angle_x", -2880, 2880)
    _validate_float_range(y, "angle_y", -2880, 2880)
    _validate_float_range(z, "angle_z", -2880, 2880)
    return _json(_osc("/beyond/master/livecontrol/angle", [x, y, z]))


@mcp.tool()
@_handle_errors
def set_master_color(red: float, green: float, blue: float) -> str:
    """Set master color RGB (0-255 each)."""
    _validate_float_range(red, "red", 0, 255)
    _validate_float_range(green, "green", 0, 255)
    _validate_float_range(blue, "blue", 0, 255)
    _check_write()
    return _json({
        "red": _client().send_osc("/beyond/master/livecontrol/red", [red]),
        "green": _client().send_osc("/beyond/master/livecontrol/green", [green]),
        "blue": _client().send_osc("/beyond/master/livecontrol/blue", [blue]),
    })


@mcp.tool()
@_handle_errors
def set_master_zoom(value: float) -> str:
    """Set master zoom (0-100)."""
    _validate_float_range(value, "zoom", 0, 100)
    return _json(_osc("/beyond/master/livecontrol/zoom", [value]))


@mcp.tool()
@_handle_errors
def set_master_scan_rate(value: float) -> str:
    """Set master scan rate (10-200)."""
    _validate_float_range(value, "scanrate", 10, 200)
    return _json(_osc("/beyond/master/livecontrol/scanrate", [value]))


# ============================================================
# Projector Control
# ============================================================


@mcp.tool()
@_handle_errors
def set_projector_size(projector_index: int, x: float, y: float) -> str:
    """Set projector output size X and Y (-100 to 100)."""
    _validate_float_range(x, "size_x", -100, 100)
    _validate_float_range(y, "size_y", -100, 100)
    _check_write()
    return _json({
        "sizex": _client().send_osc(f"/beyond/projector/{projector_index}/sizex", [x]),
        "sizey": _client().send_osc(f"/beyond/projector/{projector_index}/sizey", [y]),
    })


@mcp.tool()
@_handle_errors
def set_projector_position(projector_index: int, x: float, y: float) -> str:
    """Set projector output position X and Y (-100 to 100)."""
    _validate_float_range(x, "pos_x", -100, 100)
    _validate_float_range(y, "pos_y", -100, 100)
    _check_write()
    return _json({
        "posx": _client().send_osc(f"/beyond/projector/{projector_index}/posx", [x]),
        "posy": _client().send_osc(f"/beyond/projector/{projector_index}/posy", [y]),
    })


# ============================================================
# Server Startup
# ============================================================

_VALID_TRANSPORTS = ("stdio", "sse", "streamable-http")


def main() -> None:
    """MCP Server entry point."""
    transport = os.environ.get("BEYOND_TRANSPORT", "stdio").lower()
    if transport not in _VALID_TRANSPORTS:
        raise ValueError(
            f"Invalid BEYOND_TRANSPORT={transport!r}. "
            f"Valid options: {', '.join(_VALID_TRANSPORTS)}"
        )
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
