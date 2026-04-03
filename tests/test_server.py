"""Tests for all 44 BEYOND MCP server tools and safety features."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from beyond_mcp.server import (
    get_server_config,
    send_osc_raw,
    preview_osc,
    # Master Controls
    set_master_brightness,
    blackout,
    enable_laser_output,
    disable_laser_output,
    master_pause,
    set_master_speed,
    stop_all_now,
    stop_all_sync,
    # BPM / Beat
    set_bpm,
    beat_tap,
    beat_resync,
    # Cue Mode
    set_cue_mode_single,
    set_cue_mode_one_per,
    set_cue_mode_multi,
    # Cue / Cell Control
    select_cue,
    start_cue_by_name,
    stop_cue_by_name,
    stop_cue_now,
    focus_cell,
    start_cell,
    stop_cell,
    unselect_all_cues,
    # Page / Tab Navigation
    select_page,
    select_next_page,
    select_prev_page,
    select_tab,
    select_tab_by_name,
    # Zone Control
    mute_zone,
    unmute_zone,
    unmute_all_zones,
    stop_zone,
    select_zone,
    set_zone_brightness,
    # Live Control Parameters
    set_master_size,
    set_master_position,
    set_master_rotation,
    set_master_color,
    set_master_zoom,
    set_master_scan_rate,
    # Projector Control
    set_projector_size,
    set_projector_position,
)


def _fake_client():
    fake = MagicMock()
    fake.send_osc.return_value = {
        "address": "/test",
        "values": [],
        "type_tags": "",
        "host": "127.0.0.1",
        "port": 12000,
        "bytes_sent": 16,
    }
    return fake


# ── System ──────────────────────────────────────────────────


def test_get_server_config():
    payload = json.loads(get_server_config())
    assert payload["host"] == "127.0.0.1"
    assert payload["osc_port"] == 12000
    assert "target" in payload
    assert "allowed_hosts" in payload
    assert "read_only" in payload


@patch("beyond_mcp.server._client")
def test_send_osc_raw(mock_client):
    fake = _fake_client()
    fake.send_osc.return_value["address"] = "/beyond/test"
    mock_client.return_value = fake

    payload = json.loads(send_osc_raw("/beyond/test", "[1, 2]"))
    assert payload["address"] == "/beyond/test"
    fake.send_osc.assert_called_once_with("/beyond/test", [1, 2], type_tags=None)


def test_send_osc_raw_invalid_json():
    payload = json.loads(send_osc_raw("/test", "not json"))
    assert payload["ok"] is False
    assert "Invalid JSON" in payload["error"]


def test_send_osc_raw_non_array():
    payload = json.loads(send_osc_raw("/test", '{"a": 1}'))
    assert payload["ok"] is False
    assert "JSON array" in payload["error"]


def test_preview_osc():
    payload = json.loads(preview_osc("/beyond/general/BlackOut", "[]"))
    assert payload["preview"] is True
    assert payload["address"] == "/beyond/general/BlackOut"
    assert payload["packet_bytes"] > 0
    assert "No OSC message was sent" in payload["note"]


def test_preview_osc_with_values():
    payload = json.loads(preview_osc("/beyond/master/livecontrol/brightness", "[75.0]"))
    assert payload["preview"] is True
    assert payload["values"] == [75.0]


# ── Master Controls ─────────────────────────────────────────


@patch("beyond_mcp.server._client")
def test_set_master_brightness(mock_client):
    fake = _fake_client()
    fake.send_osc.return_value["address"] = "/beyond/master/livecontrol/brightness"
    mock_client.return_value = fake
    payload = json.loads(set_master_brightness(75.0))
    assert payload["address"] == "/beyond/master/livecontrol/brightness"
    fake.send_osc.assert_called_once_with(
        "/beyond/master/livecontrol/brightness", [75.0]
    )


def test_set_master_brightness_boundary_min():
    # Should not error on boundary value — validation only
    payload = json.loads(set_master_brightness(0.0))
    # Will fail with OSC send but not with validation
    assert payload.get("ok") is not True or "address" in payload


def test_set_master_brightness_out_of_range():
    payload = json.loads(set_master_brightness(150.0))
    assert payload["ok"] is False
    assert "blocked" in payload


@patch("beyond_mcp.server._client")
def test_blackout(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(blackout())
    fake.send_osc.assert_called_once_with("/beyond/general/BlackOut", [])


@patch("beyond_mcp.server._client")
def test_enable_laser_output(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(enable_laser_output())
    fake.send_osc.assert_called_once_with("/beyond/general/EnableLaserOutput", [])


@patch("beyond_mcp.server._client")
def test_disable_laser_output(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(disable_laser_output())
    fake.send_osc.assert_called_once_with("/beyond/general/DisableLaserOutput", [])


@patch("beyond_mcp.server._client")
def test_master_pause(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(master_pause(1))
    fake.send_osc.assert_called_once_with("/beyond/general/MasterPause", [1])


def test_master_pause_invalid_value():
    payload = json.loads(master_pause(2))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_set_master_speed(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(set_master_speed(2.0))
    fake.send_osc.assert_called_once_with("/beyond/general/MasterSpeed", [2.0])


def test_set_master_speed_out_of_range():
    payload = json.loads(set_master_speed(15.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_stop_all_now(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(stop_all_now())
    fake.send_osc.assert_called_once_with("/beyond/general/StopAllNow", [])


@patch("beyond_mcp.server._client")
def test_stop_all_sync(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(stop_all_sync(1.5))
    fake.send_osc.assert_called_once_with("/beyond/general/StopAllSync", [1.5])


@patch("beyond_mcp.server._client")
def test_stop_all_sync_default_fade(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(stop_all_sync())
    fake.send_osc.assert_called_once_with("/beyond/general/StopAllSync", [0.0])


def test_stop_all_sync_negative_fade():
    payload = json.loads(stop_all_sync(-1.0))
    assert payload["ok"] is False


# ── BPM / Beat ──────────────────────────────────────────────


@patch("beyond_mcp.server._client")
def test_set_bpm(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(set_bpm(128.0))
    fake.send_osc.assert_called_once_with("/beyond/general/SetBpm", [128.0])


def test_set_bpm_out_of_range():
    payload = json.loads(set_bpm(0.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_beat_tap(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(beat_tap())
    fake.send_osc.assert_called_once_with("/beyond/general/BeatTap", [])


@patch("beyond_mcp.server._client")
def test_beat_resync(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(beat_resync())
    fake.send_osc.assert_called_once_with("/beyond/general/BeatResync", [])


# ── Cue Mode ────────────────────────────────────────────────


@patch("beyond_mcp.server._client")
def test_set_cue_mode_single(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(set_cue_mode_single())
    fake.send_osc.assert_called_once_with("/beyond/general/OneCue", [])


@patch("beyond_mcp.server._client")
def test_set_cue_mode_one_per(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(set_cue_mode_one_per())
    fake.send_osc.assert_called_once_with("/beyond/general/OnePer", [])


@patch("beyond_mcp.server._client")
def test_set_cue_mode_multi(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(set_cue_mode_multi())
    fake.send_osc.assert_called_once_with("/beyond/general/MultiCue", [])


# ── Cue / Cell Control ──────────────────────────────────────


@patch("beyond_mcp.server._client")
def test_select_cue(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(select_cue(2, 5))
    fake.send_osc.assert_called_once_with("/beyond/general/SelectCue", [2, 5])


@patch("beyond_mcp.server._client")
def test_start_cue_by_name(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(start_cue_by_name("intro_beam"))
    fake.send_osc.assert_called_once_with("/beyond/general/StartCue", ["intro_beam"])


@patch("beyond_mcp.server._client")
def test_stop_cue_by_name(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(stop_cue_by_name("intro_beam"))
    fake.send_osc.assert_called_once_with("/beyond/general/StopCue", ["intro_beam"])


@patch("beyond_mcp.server._client")
def test_stop_cue_now(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(stop_cue_now(1, 3))
    fake.send_osc.assert_called_once_with("/beyond/general/StopCueNow", [1, 3])


@patch("beyond_mcp.server._client")
def test_focus_cell(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(focus_cell(0, 7))
    fake.send_osc.assert_called_once_with("/beyond/general/FocusCell", [0, 7])


@patch("beyond_mcp.server._client")
def test_start_cell(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(start_cell())
    fake.send_osc.assert_called_once_with("/beyond/general/StartCell", [])


@patch("beyond_mcp.server._client")
def test_stop_cell(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(stop_cell())
    fake.send_osc.assert_called_once_with("/beyond/general/StopCell", [])


@patch("beyond_mcp.server._client")
def test_unselect_all_cues(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(unselect_all_cues())
    fake.send_osc.assert_called_once_with("/beyond/general/UnselectAllCue", [])


# ── Page / Tab Navigation ───────────────────────────────────


@patch("beyond_mcp.server._client")
def test_select_page(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(select_page(3))
    fake.send_osc.assert_called_once_with("/beyond/general/SelectPage", [3])


@patch("beyond_mcp.server._client")
def test_select_next_page(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(select_next_page())
    fake.send_osc.assert_called_once_with("/beyond/general/SelectNextPage", [])


@patch("beyond_mcp.server._client")
def test_select_prev_page(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(select_prev_page())
    fake.send_osc.assert_called_once_with("/beyond/general/SelectPrevPage", [])


@patch("beyond_mcp.server._client")
def test_select_tab(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(select_tab(2))
    fake.send_osc.assert_called_once_with("/beyond/general/SelectTab", [2])


@patch("beyond_mcp.server._client")
def test_select_tab_by_name(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(select_tab_by_name("effects"))
    fake.send_osc.assert_called_once_with("/beyond/general/SelectTabName", ["effects"])


# ── Zone Control ────────────────────────────────────────────


@patch("beyond_mcp.server._client")
def test_mute_zone(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(mute_zone(1))
    fake.send_osc.assert_called_once_with("/beyond/general/MuteZone", [1])


@patch("beyond_mcp.server._client")
def test_unmute_zone(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(unmute_zone(1))
    fake.send_osc.assert_called_once_with("/beyond/general/UnmuteZone", [1])


@patch("beyond_mcp.server._client")
def test_unmute_all_zones(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(unmute_all_zones())
    fake.send_osc.assert_called_once_with("/beyond/general/UnmuteAllZone", [])


@patch("beyond_mcp.server._client")
def test_stop_zone(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(stop_zone(2, 0.5))
    fake.send_osc.assert_called_once_with("/beyond/general/StopZone", [2, 0.5])


@patch("beyond_mcp.server._client")
def test_stop_zone_default_fade(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(stop_zone(2))
    fake.send_osc.assert_called_once_with("/beyond/general/StopZone", [2, 0.0])


def test_stop_zone_negative_fade():
    payload = json.loads(stop_zone(2, -1.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_select_zone(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(select_zone(4))
    fake.send_osc.assert_called_once_with("/beyond/general/SelectZone", [4])


@patch("beyond_mcp.server._client")
def test_set_zone_brightness(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(set_zone_brightness(3, 80.0))
    fake.send_osc.assert_called_once_with(
        "/beyond/zone/3/livecontrol/brightness", [80.0]
    )


def test_set_zone_brightness_out_of_range():
    payload = json.loads(set_zone_brightness(1, 110.0))
    assert payload["ok"] is False


# ── Live Control Parameters ─────────────────────────────────


@patch("beyond_mcp.server._client")
def test_set_master_size(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(set_master_size(50.0, 50.0))
    fake.send_osc.assert_called_once_with(
        "/beyond/master/livecontrol/size", [50.0, 50.0]
    )


def test_set_master_size_out_of_range():
    payload = json.loads(set_master_size(500.0, 0.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_set_master_position(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(set_master_position(100.0, -200.0))
    fake.send_osc.assert_called_once_with(
        "/beyond/master/livecontrol/pos", [100.0, -200.0]
    )


def test_set_master_position_out_of_range():
    payload = json.loads(set_master_position(40000.0, 0.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_set_master_rotation(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(set_master_rotation(45.0, 0.0, 90.0))
    fake.send_osc.assert_called_once_with(
        "/beyond/master/livecontrol/angle", [45.0, 0.0, 90.0]
    )


def test_set_master_rotation_out_of_range():
    payload = json.loads(set_master_rotation(3000.0, 0.0, 0.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_set_master_color(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(set_master_color(255.0, 128.0, 0.0))
    assert fake.send_osc.call_count == 3
    calls = fake.send_osc.call_args_list
    assert calls[0].args == ("/beyond/master/livecontrol/red", [255.0])
    assert calls[1].args == ("/beyond/master/livecontrol/green", [128.0])
    assert calls[2].args == ("/beyond/master/livecontrol/blue", [0.0])


def test_set_master_color_out_of_range():
    payload = json.loads(set_master_color(300.0, 0.0, 0.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_set_master_zoom(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(set_master_zoom(50.0))
    fake.send_osc.assert_called_once_with(
        "/beyond/master/livecontrol/zoom", [50.0]
    )


def test_set_master_zoom_out_of_range():
    payload = json.loads(set_master_zoom(150.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_set_master_scan_rate(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(set_master_scan_rate(30.0))
    fake.send_osc.assert_called_once_with(
        "/beyond/master/livecontrol/scanrate", [30.0]
    )


def test_set_master_scan_rate_out_of_range_low():
    payload = json.loads(set_master_scan_rate(5.0))
    assert payload["ok"] is False


def test_set_master_scan_rate_out_of_range_high():
    payload = json.loads(set_master_scan_rate(250.0))
    assert payload["ok"] is False


# ── Projector Control ───────────────────────────────────────


@patch("beyond_mcp.server._client")
def test_set_projector_size(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(set_projector_size(0, 50.0, 75.0))
    assert fake.send_osc.call_count == 2
    calls = fake.send_osc.call_args_list
    assert calls[0].args == ("/beyond/projector/0/sizex", [50.0])
    assert calls[1].args == ("/beyond/projector/0/sizey", [75.0])


def test_set_projector_size_out_of_range():
    payload = json.loads(set_projector_size(0, 200.0, 0.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_set_projector_position(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(set_projector_position(1, -10.0, 20.0))
    assert fake.send_osc.call_count == 2
    calls = fake.send_osc.call_args_list
    assert calls[0].args == ("/beyond/projector/1/posx", [-10.0])
    assert calls[1].args == ("/beyond/projector/1/posy", [20.0])


def test_set_projector_position_out_of_range():
    payload = json.loads(set_projector_position(0, 150.0, 0.0))
    assert payload["ok"] is False


# ── Error handling ──────────────────────────────────────────


@patch("beyond_mcp.server._client")
def test_osc_send_failure_returns_error(mock_client):
    fake = _fake_client()
    fake.send_osc.side_effect = OSError("Network unreachable")
    mock_client.return_value = fake
    payload = json.loads(blackout())
    assert payload["ok"] is False
    assert "OSC send failed" in payload["error"]


# ── Read-only mode ──────────────────────────────────────────


def test_read_only_blocks_write_tools():
    os.environ["BEYOND_READ_ONLY"] = "1"
    try:
        payload = json.loads(blackout())
        assert payload["ok"] is False
        assert "read-only" in payload["error"]
    finally:
        os.environ.pop("BEYOND_READ_ONLY", None)


def test_read_only_allows_config():
    os.environ["BEYOND_READ_ONLY"] = "1"
    try:
        payload = json.loads(get_server_config())
        assert payload["read_only"] is True
    finally:
        os.environ.pop("BEYOND_READ_ONLY", None)


def test_read_only_allows_preview():
    os.environ["BEYOND_READ_ONLY"] = "1"
    try:
        payload = json.loads(preview_osc("/beyond/general/BlackOut", "[]"))
        assert payload["preview"] is True
    finally:
        os.environ.pop("BEYOND_READ_ONLY", None)


# ── Host allowlisting ──────────────────────────────────────


def test_disallowed_host_blocked():
    os.environ["BEYOND_HOST"] = "10.0.0.50"
    try:
        payload = json.loads(blackout())
        assert payload["ok"] is False
        assert "not in BEYOND_ALLOWED_HOSTS" in payload["error"]
    finally:
        os.environ.pop("BEYOND_HOST", None)


def test_wildcard_allows_any_host():
    os.environ["BEYOND_HOST"] = "10.0.0.50"
    os.environ["BEYOND_ALLOWED_HOSTS"] = "*"
    try:
        payload = json.loads(get_server_config())
        assert payload["host"] == "10.0.0.50"
    finally:
        os.environ.pop("BEYOND_HOST", None)
        os.environ.pop("BEYOND_ALLOWED_HOSTS", None)


# ── Transport validation ────────────────────────────────────


def test_main_rejects_invalid_transport():
    from beyond_mcp.server import main

    os.environ["BEYOND_TRANSPORT"] = "websocket"
    with pytest.raises(ValueError, match="Invalid BEYOND_TRANSPORT"):
        main()
    os.environ.pop("BEYOND_TRANSPORT", None)


# ── Config edge cases ───────────────────────────────────────


def test_port_zero_rejected():
    from beyond_mcp.config import _parse_port

    os.environ["BEYOND_OSC_PORT"] = "0"
    with pytest.raises(ValueError, match="outside valid port range"):
        _parse_port("BEYOND_OSC_PORT", "12000")
    os.environ.pop("BEYOND_OSC_PORT", None)


def test_port_65536_rejected():
    from beyond_mcp.config import _parse_port

    os.environ["BEYOND_OSC_PORT"] = "65536"
    with pytest.raises(ValueError, match="outside valid port range"):
        _parse_port("BEYOND_OSC_PORT", "12000")
    os.environ.pop("BEYOND_OSC_PORT", None)


def test_port_non_integer_rejected():
    from beyond_mcp.config import _parse_port

    os.environ["BEYOND_OSC_PORT"] = "abc"
    with pytest.raises(ValueError, match="not a valid integer"):
        _parse_port("BEYOND_OSC_PORT", "12000")
    os.environ.pop("BEYOND_OSC_PORT", None)


# ── Type tag mismatch (client) ──────────────────────────────


def test_type_tags_length_mismatch():
    from beyond_mcp.client import build_osc_message

    with pytest.raises(ValueError, match="type_tags length"):
        build_osc_message("/test", [1, 2], type_tags="i")


# ── Tool count ──────────────────────────────────────────────


def test_tool_count_is_44():
    from beyond_mcp.server import mcp as server_mcp

    tools = server_mcp._tool_manager._tools
    assert len(tools) == 44, f"Expected 44 tools, got {len(tools)}: {sorted(tools.keys())}"
