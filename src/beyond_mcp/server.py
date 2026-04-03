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

from .client import BeyondClient, build_osc_bundle, build_osc_message
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


_DESTRUCTIVE_TOOLS = frozenset({
    "blackout", "stop_all_now", "stop_all_sync", "stop_all_async",
    "disable_laser_output", "stop_zones_of_projector",
    "stop_zone", "stop_zone_by_name", "stop_projector_by_name",
    "load_workspace",
})

_DESTRUCTIVE_OSC_ADDRESSES = frozenset({
    "/beyond/general/BlackOut",
    "/beyond/general/DisableLaserOutput",
    "/beyond/general/StopAllNow",
    "/beyond/general/StopAllSync",
    "/beyond/general/StopAllAsync",
    "/beyond/general/StopZone",
    "/beyond/general/StopZoneByName",
    "/beyond/general/StopZonesOfProjector",
    "/beyond/general/StopProjectorByName",
    "/beyond/general/LoadWorkspace",
})


def _check_destructive(tool_name: str, confirm: bool) -> None:
    _check_write()
    config = load_config()
    if config.confirm_destructive and not confirm:
        raise ValueError(
            f"Destructive operation '{tool_name}' requires confirm=true "
            f"(BEYOND_CONFIRM_DESTRUCTIVE is enabled)."
        )


def _check_destructive_address(address: str, confirm: bool) -> None:
    _check_write()
    config = load_config()
    if config.confirm_destructive and address in _DESTRUCTIVE_OSC_ADDRESSES and not confirm:
        raise ValueError(
            f"Destructive OSC address {address!r} requires confirm=true "
            f"(BEYOND_CONFIRM_DESTRUCTIVE is enabled)."
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


def _validate_non_negative_int(value: int, name: str) -> None:
    if value < 0:
        raise ValueError(f"{name} must be >= 0, got {value}")


def _validate_string_choice(value: str, name: str, choices: set[str]) -> None:
    if value not in choices:
        raise ValueError(f"{name} must be one of {sorted(choices)}, got {value!r}")


def _optional_timetag(value: int) -> int | None:
    if value < 0:
        return None
    return value


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
        "safety_profile": config.safety_profile,
        "read_only": config.read_only,
        "confirm_destructive": config.confirm_destructive,
    })


@mcp.tool()
@_handle_errors
def health_check() -> str:
    """Check if the BEYOND target is reachable (DNS resolution + UDP socket)."""
    return _json(_client().health_check())


@mcp.tool()
@_handle_errors
def send_osc_raw(address: str, values_json: str = "[]", type_tags: str = "", confirm: bool = False) -> str:
    """Send a raw OSC message to BEYOND. Use for any address not wrapped by a named tool."""
    _check_destructive_address(address, confirm)
    values = json.loads(values_json)
    if not isinstance(values, list):
        raise ValueError("values_json must be a JSON array.")
    result = _client().send_osc(address, values, type_tags=type_tags or None)
    return _json(result)


@mcp.tool()
@_handle_errors
def send_osc_bundle(messages_json: str, confirm: bool = False, timetag: int = -1) -> str:
    """Send multiple OSC messages as an atomic bundle.

    messages_json: JSON array of [address, values] pairs.
    Example: '[[\"/beyond/general/BlackOut\", []], [\"/beyond/general/SetBpm\", [120]]]'
    """
    _check_write()
    messages = json.loads(messages_json)
    if not isinstance(messages, list):
        raise ValueError("messages_json must be a JSON array.")
    pairs = []
    for i, entry in enumerate(messages):
        if not isinstance(entry, list) or len(entry) != 2:
            raise ValueError(f"Entry {i} must be [address, values_array].")
        addr, vals = entry
        if not isinstance(addr, str) or not isinstance(vals, list):
            raise ValueError(f"Entry {i}: address must be string, values must be array.")
        _check_destructive_address(addr, confirm)
        pairs.append((addr, vals))
    result = _client().send_bundle(pairs, timetag=_optional_timetag(timetag))
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


@mcp.tool()
@_handle_errors
def preview_osc_bundle(messages_json: str, timetag: int = -1) -> str:
    """Preview an OSC bundle without sending it."""
    messages = json.loads(messages_json)
    if not isinstance(messages, list):
        raise ValueError("messages_json must be a JSON array.")
    packets = []
    parsed_messages = []
    for i, entry in enumerate(messages):
        if not isinstance(entry, list) or len(entry) != 2:
            raise ValueError(f"Entry {i} must be [address, values_array].")
        addr, vals = entry
        if not isinstance(addr, str) or not isinstance(vals, list):
            raise ValueError(f"Entry {i}: address must be string, values must be array.")
        packets.append(build_osc_message(addr, vals))
        parsed_messages.append({"address": addr, "values": vals})
    config = load_config()
    bundle = build_osc_bundle(packets, timetag=_optional_timetag(timetag))
    return _json({
        "preview": True,
        "bundle": True,
        "message_count": len(parsed_messages),
        "messages": parsed_messages,
        "target_host": config.host,
        "target_port": config.osc_port,
        "timetag": _optional_timetag(timetag) if _optional_timetag(timetag) is not None else 1,
        "packet_bytes": len(bundle),
        "note": "This is a preview only. No OSC bundle was sent.",
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
def blackout(confirm: bool = False) -> str:
    """Activate blackout — disable all laser output. Set confirm=true when BEYOND_CONFIRM_DESTRUCTIVE is enabled."""
    _check_destructive("blackout", confirm)
    return _json(_osc("/beyond/general/BlackOut", []))


@mcp.tool()
@_handle_errors
def enable_laser_output() -> str:
    """Enable laser output (undo blackout)."""
    return _json(_osc("/beyond/general/EnableLaserOutput", []))


@mcp.tool()
@_handle_errors
def disable_laser_output(confirm: bool = False) -> str:
    """Disable laser output. Set confirm=true when BEYOND_CONFIRM_DESTRUCTIVE is enabled."""
    _check_destructive("disable_laser_output", confirm)
    return _json(_osc("/beyond/general/DisableLaserOutput", []))


@mcp.tool()
@_handle_errors
def master_pause(enabled: int) -> str:
    """Pause or unpause master playback. 1=pause, 0=unpause."""
    _validate_int_choice(enabled, "enabled", {0, 1})
    return _json(_osc("/beyond/general/MasterPause", [enabled]))


@mcp.tool()
@_handle_errors
def master_pause_time(enabled: int) -> str:
    """Pause or unpause master playback with time sync. 1=pause, 0=unpause."""
    _validate_int_choice(enabled, "enabled", {0, 1})
    return _json(_osc("/beyond/general/MasterPauseTime", [enabled]))


@mcp.tool()
@_handle_errors
def set_master_speed(value: float) -> str:
    """Set master playback speed (0-10)."""
    _validate_float_range(value, "speed", 0, 10)
    return _json(_osc("/beyond/general/MasterSpeed", [value]))


@mcp.tool()
@_handle_errors
def stop_all_now(confirm: bool = False) -> str:
    """Stop all playback immediately. Set confirm=true when BEYOND_CONFIRM_DESTRUCTIVE is enabled."""
    _check_destructive("stop_all_now", confirm)
    return _json(_osc("/beyond/general/StopAllNow", []))


@mcp.tool()
@_handle_errors
def stop_all_sync(fade_time: float = 0.0, confirm: bool = False) -> str:
    """Stop all playback with synchronization fade. Set confirm=true when BEYOND_CONFIRM_DESTRUCTIVE is enabled."""
    _validate_non_negative(fade_time, "fade_time")
    _check_destructive("stop_all_sync", confirm)
    return _json(_osc("/beyond/general/StopAllSync", [fade_time]))


@mcp.tool()
@_handle_errors
def stop_all_async(fade_time: float = 0.0, confirm: bool = False) -> str:
    """Stop all playback asynchronously with fade. Set confirm=true when BEYOND_CONFIRM_DESTRUCTIVE is enabled."""
    _validate_non_negative(fade_time, "fade_time")
    _check_destructive("stop_all_async", confirm)
    return _json(_osc("/beyond/general/StopAllAsync", [fade_time]))


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
def set_bpm_delta(delta: float) -> str:
    """Adjust BPM by a delta value."""
    return _json(_osc("/beyond/general/SetBpmDelta", [delta]))


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


@mcp.tool()
@_handle_errors
def beat_source_timer() -> str:
    """Set beat source to internal timer."""
    return _json(_osc("/beyond/general/TimerBeat", []))


@mcp.tool()
@_handle_errors
def beat_source_audio() -> str:
    """Set beat source to audio input."""
    return _json(_osc("/beyond/general/AudioBeat", []))


@mcp.tool()
@_handle_errors
def beat_source_manual() -> str:
    """Set beat source to manual tap."""
    return _json(_osc("/beyond/general/ManualBeat", []))


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
# Click Behavior
# ============================================================


@mcp.tool()
@_handle_errors
def click_mode_select() -> str:
    """Set click behavior to Select mode."""
    return _json(_osc("/beyond/general/ClickSelect", []))


@mcp.tool()
@_handle_errors
def click_mode_toggle() -> str:
    """Set click behavior to Toggle mode."""
    return _json(_osc("/beyond/general/ClickToggle", []))


@mcp.tool()
@_handle_errors
def click_mode_restart() -> str:
    """Set click behavior to Restart mode."""
    return _json(_osc("/beyond/general/ClickRestart", []))


@mcp.tool()
@_handle_errors
def click_mode_flash() -> str:
    """Set click behavior to Flash mode."""
    return _json(_osc("/beyond/general/ClickFlash", []))


@mcp.tool()
@_handle_errors
def click_mode_solo_flash() -> str:
    """Set click behavior to Solo Flash mode."""
    return _json(_osc("/beyond/general/ClickSoloFlash", []))


@mcp.tool()
@_handle_errors
def click_mode_live() -> str:
    """Set click behavior to Live mode."""
    return _json(_osc("/beyond/general/ClickLive", []))


_CLICK_SCROLL_PARAMS = {
    "zoom": "ClickScrollZoom",
    "size": "ClickScrollSize",
    "fade": "ClickScrollFade",
    "vpoints": "ClickScrollVPoints",
    "scanrate": "ClickScrollScanRate",
    "color": "ClickScrollColor",
    "anispeed": "ClickScrollAniSpeed",
    "red": "ClickScrollR",
    "green": "ClickScrollG",
    "blue": "ClickScrollB",
    "alpha": "ClickScrollA",
}


@mcp.tool()
@_handle_errors
def set_click_scroll(parameter: str, value: float) -> str:
    """Set a click-scroll parameter. Parameters: zoom, size, fade, vpoints, scanrate, color, anispeed, red, green, blue, alpha."""
    _validate_string_choice(parameter, "parameter", set(_CLICK_SCROLL_PARAMS.keys()))
    return _json(_osc(f"/beyond/general/{_CLICK_SCROLL_PARAMS[parameter]}", [value]))


# ============================================================
# Transitions
# ============================================================


@mcp.tool()
@_handle_errors
def set_transition_type(index: int) -> str:
    """Set the transition type by index."""
    return _json(_osc("/beyond/general/Transition", [index]))


@mcp.tool()
@_handle_errors
def set_master_transition_index(index: int) -> str:
    """Set the master transition effect index."""
    return _json(_osc("/beyond/general/MasterTransitionIndex", [index]))


@mcp.tool()
@_handle_errors
def set_master_transition_time(time: float) -> str:
    """Set the master transition time in seconds."""
    _validate_non_negative(time, "time")
    return _json(_osc("/beyond/general/MasterTransitionTime", [time]))


# ============================================================
# Cue / Cell Control
# ============================================================


@mcp.tool()
@_handle_errors
def select_cue(name: str) -> str:
    """Select a cue by name."""
    return _json(_osc("/beyond/general/SelectCue", [name]))


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
def stop_cue_sync(page: int, cue: int, fade_time: float = 0.0) -> str:
    """Stop a specific cue with synchronization fade."""
    _validate_non_negative(fade_time, "fade_time")
    return _json(_osc("/beyond/general/StopCueSync", [page, cue, fade_time]))


@mcp.tool()
@_handle_errors
def cue_down(page: int, cue: int, count: int = 1) -> str:
    """Navigate cue selection downward."""
    return _json(_osc("/beyond/general/CueDown", [page, cue, count]))


@mcp.tool()
@_handle_errors
def cue_up(page: int, cue: int, count: int = 1) -> str:
    """Navigate cue selection upward."""
    return _json(_osc("/beyond/general/CueUp", [page, cue, count]))


@mcp.tool()
@_handle_errors
def pause_cue(page: int, cue: int, state: int) -> str:
    """Pause or unpause a cue. state: 1=pause, 0=unpause."""
    _validate_int_choice(state, "state", {0, 1})
    return _json(_osc("/beyond/general/PauseCue", [page, cue, state]))


@mcp.tool()
@_handle_errors
def restart_cue(page: int, cue: int) -> str:
    """Restart a cue from the beginning."""
    return _json(_osc("/beyond/general/RestartCue", [page, cue]))


@mcp.tool()
@_handle_errors
def focus_cell(page: int, cue: int) -> str:
    """Focus on a cell by page and cue coordinates."""
    return _json(_osc("/beyond/general/FocusCell", [page, cue]))


@mcp.tool()
@_handle_errors
def focus_cell_index(index: int) -> str:
    """Focus on a cell by linear index."""
    return _json(_osc("/beyond/general/FocusCellIndex", [index]))


@mcp.tool()
@_handle_errors
def start_cell() -> str:
    """Start the currently focused cell."""
    return _json(_osc("/beyond/general/StartCell", []))


@mcp.tool()
@_handle_errors
def restart_cell() -> str:
    """Restart the currently focused cell."""
    return _json(_osc("/beyond/general/ReStartCell", []))


@mcp.tool()
@_handle_errors
def stop_cell() -> str:
    """Stop the currently focused cell."""
    return _json(_osc("/beyond/general/StopCell", []))


@mcp.tool()
@_handle_errors
def shift_focus(direction: int) -> str:
    """Shift cell focus by direction offset."""
    return _json(_osc("/beyond/general/ShiftFocus", [direction]))


@mcp.tool()
@_handle_errors
def move_focus(dx: int, dy: int) -> str:
    """Move cell focus by delta X and Y."""
    return _json(_osc("/beyond/general/MoveFocus", [dx, dy]))


@mcp.tool()
@_handle_errors
def unselect_all_cues() -> str:
    """Deselect all active cues."""
    return _json(_osc("/beyond/general/UnselectAllCue", []))


# ============================================================
# Workspace
# ============================================================


@mcp.tool()
@_handle_errors
def load_cue(name: str) -> str:
    """Load a cue by name without starting it."""
    return _json(_osc("/beyond/general/LoadCue", [name]))


@mcp.tool()
@_handle_errors
def load_workspace(name: str, confirm: bool = False) -> str:
    """Load a workspace by name."""
    _check_destructive("load_workspace", confirm)
    return _json(_osc("/beyond/general/LoadWorkspace", [name]))


# ============================================================
# Page / Tab / Category Navigation
# ============================================================


@mcp.tool()
@_handle_errors
def select_page(page_index: int) -> str:
    """Select a page by index."""
    _validate_non_negative_int(page_index, "page_index")
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
    _validate_non_negative_int(tab_index, "tab_index")
    return _json(_osc("/beyond/general/SelectTab", [tab_index]))


@mcp.tool()
@_handle_errors
def select_tab_by_name(name: str) -> str:
    """Select a tab by name."""
    return _json(_osc("/beyond/general/SelectTabName", [name]))


@mcp.tool()
@_handle_errors
def select_next_tab() -> str:
    """Navigate to the next tab."""
    return _json(_osc("/beyond/general/SelectNextTab", []))


@mcp.tool()
@_handle_errors
def select_prev_tab() -> str:
    """Navigate to the previous tab."""
    return _json(_osc("/beyond/general/SelectPrevTab", []))


@mcp.tool()
@_handle_errors
def select_all_categories() -> str:
    """Select all content categories."""
    return _json(_osc("/beyond/general/SelectAllCat", []))


@mcp.tool()
@_handle_errors
def select_category(index: int) -> str:
    """Select a content category by index."""
    _validate_non_negative_int(index, "index")
    return _json(_osc("/beyond/general/SelectCat", [index]))


@mcp.tool()
@_handle_errors
def select_category_by_name(name: str) -> str:
    """Select a content category by name."""
    return _json(_osc("/beyond/general/SelectCatName", [name]))


@mcp.tool()
@_handle_errors
def select_next_category() -> str:
    """Navigate to the next content category."""
    return _json(_osc("/beyond/general/SelectNextCat", []))


@mcp.tool()
@_handle_errors
def select_prev_category() -> str:
    """Navigate to the previous content category."""
    return _json(_osc("/beyond/general/SelectPrevCat", []))


# ============================================================
# Grid Management
# ============================================================


@mcp.tool()
@_handle_errors
def set_grid_size(columns: int, rows: int) -> str:
    """Set the cue grid dimensions."""
    _validate_non_negative_int(columns, "columns")
    _validate_non_negative_int(rows, "rows")
    return _json(_osc("/beyond/general/SetGridSize", [columns, rows]))


@mcp.tool()
@_handle_errors
def select_grid(index: int) -> str:
    """Select a grid by index."""
    _validate_non_negative_int(index, "index")
    return _json(_osc("/beyond/general/SelectGrid", [index]))


# ============================================================
# Zone Control
# ============================================================


@mcp.tool()
@_handle_errors
def mute_zone(zone_index: int) -> str:
    """Mute a projection zone by index."""
    _validate_non_negative_int(zone_index, "zone_index")
    return _json(_osc("/beyond/general/MuteZone", [zone_index]))


@mcp.tool()
@_handle_errors
def unmute_zone(zone_index: int) -> str:
    """Unmute a projection zone by index."""
    _validate_non_negative_int(zone_index, "zone_index")
    return _json(_osc("/beyond/general/UnmuteZone", [zone_index]))


@mcp.tool()
@_handle_errors
def toggle_mute_zone(zone_index: int) -> str:
    """Toggle mute state for a projection zone."""
    _validate_non_negative_int(zone_index, "zone_index")
    return _json(_osc("/beyond/general/ToggleMuteZone", [zone_index]))


@mcp.tool()
@_handle_errors
def unmute_all_zones() -> str:
    """Unmute all projection zones."""
    return _json(_osc("/beyond/general/UnmuteAllZone", []))


@mcp.tool()
@_handle_errors
def stop_zone(zone_index: int, fade_time: float = 0.0, confirm: bool = False) -> str:
    """Stop output on a zone with optional fade time."""
    _check_destructive("stop_zone", confirm)
    _validate_non_negative_int(zone_index, "zone_index")
    _validate_non_negative(fade_time, "fade_time")
    return _json(_osc("/beyond/general/StopZone", [zone_index, fade_time]))


@mcp.tool()
@_handle_errors
def stop_zone_by_name(name: str, confirm: bool = False) -> str:
    """Stop output on a zone by name."""
    _check_destructive("stop_zone_by_name", confirm)
    return _json(_osc("/beyond/general/StopZoneByName", [name]))


@mcp.tool()
@_handle_errors
def stop_zones_of_projector(projector_index: int, confirm: bool = False) -> str:
    """Stop all zones assigned to a projector. Set confirm=true when BEYOND_CONFIRM_DESTRUCTIVE is enabled."""
    _check_destructive("stop_zones_of_projector", confirm)
    _validate_non_negative_int(projector_index, "projector_index")
    return _json(_osc("/beyond/general/StopZonesOfProjector", [projector_index]))


@mcp.tool()
@_handle_errors
def stop_projector_by_name(name: str, confirm: bool = False) -> str:
    """Stop all zones of a projector by name."""
    _check_destructive("stop_projector_by_name", confirm)
    return _json(_osc("/beyond/general/StopProjectorByName", [name]))


@mcp.tool()
@_handle_errors
def select_zone(zone_index: int) -> str:
    """Select a projection zone."""
    _validate_non_negative_int(zone_index, "zone_index")
    return _json(_osc("/beyond/general/SelectZone", [zone_index]))


@mcp.tool()
@_handle_errors
def select_zone_by_name(name: str) -> str:
    """Select a projection zone by name."""
    return _json(_osc("/beyond/general/SelectZoneName", [name]))


@mcp.tool()
@_handle_errors
def unselect_zone(zone_index: int) -> str:
    """Unselect a projection zone."""
    _validate_non_negative_int(zone_index, "zone_index")
    return _json(_osc("/beyond/general/UnSelectZone", [zone_index]))


@mcp.tool()
@_handle_errors
def unselect_all_zones() -> str:
    """Unselect all projection zones."""
    return _json(_osc("/beyond/general/UnselectAllZones", []))


@mcp.tool()
@_handle_errors
def toggle_select_zone(zone_index: int) -> str:
    """Toggle selection state for a projection zone."""
    _validate_non_negative_int(zone_index, "zone_index")
    return _json(_osc("/beyond/general/ToggleSelectZone", [zone_index]))


@mcp.tool()
@_handle_errors
def store_zone_selection() -> str:
    """Store the current zone selection for later recall."""
    return _json(_osc("/beyond/general/StoreZoneSelection", []))


@mcp.tool()
@_handle_errors
def restore_zone_selection() -> str:
    """Restore a previously stored zone selection."""
    return _json(_osc("/beyond/general/ReStoreZoneSelection", []))


@mcp.tool()
@_handle_errors
def set_zone_brightness(zone_index: int, value: float) -> str:
    """Set brightness for a specific zone (0-100)."""
    _validate_non_negative_int(zone_index, "zone_index")
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
def set_master_rotation_speed(x: float, y: float, z: float) -> str:
    """Set master continuous rotation speed X, Y, Z (-1440 to 1440, in degrees/sec)."""
    _validate_float_range(x, "roto_x", -1440, 1440)
    _validate_float_range(y, "roto_y", -1440, 1440)
    _validate_float_range(z, "roto_z", -1440, 1440)
    return _json(_osc("/beyond/master/livecontrol/roto", [x, y, z]))


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
def set_master_alpha(value: float) -> str:
    """Set master alpha/opacity (0-255)."""
    _validate_float_range(value, "alpha", 0, 255)
    return _json(_osc("/beyond/master/livecontrol/alpha", [value]))


@mcp.tool()
@_handle_errors
def set_master_zoom(value: float) -> str:
    """Set master zoom (0-100)."""
    _validate_float_range(value, "zoom", 0, 100)
    return _json(_osc("/beyond/master/livecontrol/zoom", [value]))


@mcp.tool()
@_handle_errors
def set_master_scan_rate(value: float) -> str:
    """Set master scan rate (10-200, default 100)."""
    _validate_float_range(value, "scanrate", 10, 200)
    return _json(_osc("/beyond/master/livecontrol/scanrate", [value]))


@mcp.tool()
@_handle_errors
def set_master_visible_points(value: float) -> str:
    """Set master visible points percentage (0-100)."""
    _validate_float_range(value, "visiblepoints", 0, 100)
    return _json(_osc("/beyond/master/livecontrol/visiblepoints", [value]))


@mcp.tool()
@_handle_errors
def set_master_color_slider(value: float) -> str:
    """Set master color slider (0-255)."""
    _validate_float_range(value, "colorslider", 0, 255)
    return _json(_osc("/beyond/master/livecontrol/colorslider", [value]))


@mcp.tool()
@_handle_errors
def set_master_animation_speed(value: float) -> str:
    """Set master animation speed (0-400)."""
    _validate_float_range(value, "anispeed", 0, 400)
    return _json(_osc("/beyond/master/livecontrol/anispeed", [value]))


# ============================================================
# Live Control: Effects (Master scope)
# ============================================================


@mcp.tool()
@_handle_errors
def set_master_effect(slot: int, effect_index: int) -> str:
    """Set an effect on a master FX slot (slot 1-4, effect_index -1..47, -1=stop)."""
    _validate_int_choice(slot, "slot", {1, 2, 3, 4})
    _validate_float_range(float(effect_index), "effect_index", -1, 47)
    return _json(_osc(f"/beyond/master/livecontrol/fx{slot}", [float(effect_index)]))


@mcp.tool()
@_handle_errors
def set_master_effect_action(slot: int, value: float) -> str:
    """Set the action/intensity of a master FX slot (slot 1-4, value 0-100)."""
    _validate_int_choice(slot, "slot", {1, 2, 3, 4})
    _validate_float_range(value, "value", 0, 100)
    return _json(_osc(f"/beyond/master/livecontrol/fx{slot}action", [value]))


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


@mcp.tool()
@_handle_errors
def projector_swap_xy(projector_index: int, state: int) -> str:
    """Toggle projector X/Y axis swap. 0=off, 1=on, 2=toggle."""
    _validate_int_choice(state, "state", {0, 1, 2})
    return _json(_osc(f"/beyond/projector/{projector_index}/swapxy", [float(state)]))


@mcp.tool()
@_handle_errors
def projector_invert_x(projector_index: int, state: int) -> str:
    """Toggle projector X-axis inversion. 0=off, 1=on, 2=toggle."""
    _validate_int_choice(state, "state", {0, 1, 2})
    return _json(_osc(f"/beyond/projector/{projector_index}/invx", [float(state)]))


@mcp.tool()
@_handle_errors
def projector_invert_y(projector_index: int, state: int) -> str:
    """Toggle projector Y-axis inversion. 0=off, 1=on, 2=toggle."""
    _validate_int_choice(state, "state", {0, 1, 2})
    return _json(_osc(f"/beyond/projector/{projector_index}/invy", [float(state)]))


# ============================================================
# Zone Setup / Geometric Correction
# ============================================================

_ZONE_SETUP_PARAMS = {
    "xsize", "ysize", "xposition", "yposition", "zrotation",
    "xlinearity", "ylinearity", "xsymmetry", "ysymmetry",
    "xsymmetryoffset", "ysymmetryoffset", "xkeystone", "ykeystone",
    "xpincussion", "ypincussion", "xpincussionoffset", "ypincussionoffset",
    "xbow", "ybow", "xbowoffset", "ybowoffset", "xshear", "yshear",
    "ax", "ay", "bx", "by", "x", "y",
}


@mcp.tool()
@_handle_errors
def zone_setup_select(zone_index: int) -> str:
    """Select a zone for geometric setup."""
    return _json(_osc("/beyond/zonesetup/zone", [float(zone_index)]))


@mcp.tool()
@_handle_errors
def zone_setup_next_zone() -> str:
    """Navigate to the next zone in setup."""
    return _json(_osc("/beyond/zonesetup/nextzone", []))


@mcp.tool()
@_handle_errors
def zone_setup_prev_zone() -> str:
    """Navigate to the previous zone in setup."""
    return _json(_osc("/beyond/zonesetup/prevzone", []))


@mcp.tool()
@_handle_errors
def zone_setup_select_param(param_index: int) -> str:
    """Select a geometric parameter by index for editing."""
    return _json(_osc("/beyond/zonesetup/param", [float(param_index)]))


@mcp.tool()
@_handle_errors
def zone_setup_next_param() -> str:
    """Navigate to the next geometric parameter."""
    return _json(_osc("/beyond/zonesetup/nextparam", []))


@mcp.tool()
@_handle_errors
def zone_setup_prev_param() -> str:
    """Navigate to the previous geometric parameter."""
    return _json(_osc("/beyond/zonesetup/prevparam", []))


@mcp.tool()
@_handle_errors
def zone_setup_set(parameter: str, value: float) -> str:
    """Set a zone geometric correction parameter. Parameters: xsize, ysize, xposition, yposition, zrotation, xlinearity, ylinearity, xsymmetry, ysymmetry, xkeystone, ykeystone, xpincussion, ypincussion, xbow, ybow, xshear, yshear, ax, ay, bx, by, and more."""
    _validate_string_choice(parameter, "parameter", _ZONE_SETUP_PARAMS)
    return _json(_osc(f"/beyond/zonesetup/{parameter}", [value]))


# ============================================================
# Safety Limiter
# ============================================================

_LIMITER_TYPES = {
    "profile": "SetLimiterProfile",
    "per_zone": "SetLimiterPerZone",
    "per_grid": "SetLimiterPerGrid",
    "flash": "SetLimiterFlash",
    "hold": "SetLimiterHold",
    "beam": "SetLimiterBeam",
    "dmx": "SetLimiterDMX",
    "show": "SetLimiterShow",
}


@mcp.tool()
@_handle_errors
def set_limiter(limiter_type: str, value: int) -> str:
    """Set a safety limiter. Types: profile, per_zone, per_grid, flash, hold, beam, dmx, show."""
    _validate_string_choice(limiter_type, "limiter_type", set(_LIMITER_TYPES.keys()))
    return _json(_osc(f"/beyond/general/{_LIMITER_TYPES[limiter_type]}", [value]))


# ============================================================
# Display
# ============================================================


@mcp.tool()
@_handle_errors
def display_popup(message: str) -> str:
    """Display a popup message in BEYOND."""
    return _json(_osc("/beyond/general/DisplayPopup", [message]))


@mcp.tool()
@_handle_errors
def display_preview(name: str, enabled: int) -> str:
    """Show or hide a named preview window. 1=show, 0=hide."""
    _validate_int_choice(enabled, "enabled", {0, 1})
    return _json(_osc("/beyond/general/DisplayPreview", [name, enabled]))


# ============================================================
# DMX / Channel Output
# ============================================================


@mcp.tool()
@_handle_errors
def channel_out(channel: int, value: int) -> str:
    """Send a value to a BEYOND output channel."""
    return _json(_osc("/beyond/general/ChannelOut", [channel, value]))


# ============================================================
# Control Scope
# ============================================================

_CONTROL_SCOPES = {
    "master": ("ControlMaster", False),
    "cue": ("ControlCue", True),       # requires page, cue indices
    "zone": ("ControlZone", True),      # requires zone index
    "track": ("ControlTrack", True),    # requires track index
    "projector": ("ControlProjector", True),  # requires projector index
    "smart": ("ControlSmart", True),    # requires smart index
}


@mcp.tool()
@_handle_errors
def set_control_scope(scope: str, index1: int = 0, index2: int = 0) -> str:
    """Set the live control target scope. Scopes: master, cue (page+cue), zone, track, projector, smart."""
    _validate_string_choice(scope, "scope", set(_CONTROL_SCOPES.keys()))
    cmd, needs_index = _CONTROL_SCOPES[scope]
    if scope == "cue":
        return _json(_osc(f"/beyond/general/{cmd}", [index1, index2]))
    elif needs_index:
        return _json(_osc(f"/beyond/general/{cmd}", [index1]))
    else:
        return _json(_osc(f"/beyond/general/{cmd}", []))


# ============================================================
# Virtual LJ
# ============================================================


@mcp.tool()
@_handle_errors
def virtual_lj(enabled: int) -> str:
    """Enable or disable Virtual LJ mode. 1=enable, 0=disable."""
    _validate_int_choice(enabled, "enabled", {0, 1})
    return _json(_osc("/beyond/general/VirtualLJ", [enabled]))


@mcp.tool()
@_handle_errors
def virtual_lj_fx(lj_index: int, fx_index: int) -> str:
    """Trigger a Virtual LJ effect."""
    return _json(_osc("/beyond/general/VLJFX", [lj_index, fx_index]))


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
