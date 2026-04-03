"""Tests for all 117 BEYOND MCP server tools and safety features."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from beyond_mcp.server import (
    # System
    get_server_config,
    health_check,
    send_osc_raw,
    send_osc_bundle,
    preview_osc,
    preview_osc_bundle,
    # Master Controls
    set_master_brightness,
    blackout,
    enable_laser_output,
    disable_laser_output,
    master_pause,
    master_pause_time,
    set_master_speed,
    stop_all_now,
    stop_all_sync,
    stop_all_async,
    # BPM / Beat
    set_bpm,
    set_bpm_delta,
    beat_tap,
    beat_resync,
    beat_source_timer,
    beat_source_audio,
    beat_source_manual,
    # Cue Mode
    set_cue_mode_single,
    set_cue_mode_one_per,
    set_cue_mode_multi,
    # Click Behavior
    click_mode_select,
    click_mode_toggle,
    click_mode_restart,
    click_mode_flash,
    click_mode_solo_flash,
    click_mode_live,
    set_click_scroll,
    # Transitions
    set_transition_type,
    set_master_transition_index,
    set_master_transition_time,
    # Cue / Cell Control
    select_cue,
    start_cue_by_name,
    stop_cue_by_name,
    stop_cue_now,
    stop_cue_sync,
    cue_down,
    cue_up,
    pause_cue,
    restart_cue,
    focus_cell,
    focus_cell_index,
    start_cell,
    restart_cell,
    stop_cell,
    shift_focus,
    move_focus,
    unselect_all_cues,
    # Workspace
    load_cue,
    load_workspace,
    # Page / Tab / Category Navigation
    select_page,
    select_next_page,
    select_prev_page,
    select_tab,
    select_tab_by_name,
    select_next_tab,
    select_prev_tab,
    select_all_categories,
    select_category,
    select_category_by_name,
    select_next_category,
    select_prev_category,
    # Grid Management
    set_grid_size,
    select_grid,
    # Zone Control
    mute_zone,
    unmute_zone,
    toggle_mute_zone,
    unmute_all_zones,
    stop_zone,
    stop_zone_by_name,
    stop_zones_of_projector,
    stop_projector_by_name,
    select_zone,
    select_zone_by_name,
    unselect_zone,
    unselect_all_zones,
    toggle_select_zone,
    store_zone_selection,
    restore_zone_selection,
    set_zone_brightness,
    # Live Control Parameters (Master)
    set_master_size,
    set_master_position,
    set_master_rotation,
    set_master_rotation_speed,
    set_master_color,
    set_master_alpha,
    set_master_zoom,
    set_master_scan_rate,
    set_master_visible_points,
    set_master_color_slider,
    set_master_animation_speed,
    # Effects
    set_master_effect,
    set_master_effect_action,
    # Projector Control
    set_projector_size,
    set_projector_position,
    projector_swap_xy,
    projector_invert_x,
    projector_invert_y,
    # Zone Setup / Geometric Correction
    zone_setup_select,
    zone_setup_next_zone,
    zone_setup_prev_zone,
    zone_setup_select_param,
    zone_setup_next_param,
    zone_setup_prev_param,
    zone_setup_set,
    # Safety Limiter
    set_limiter,
    # Display
    display_popup,
    display_preview,
    # DMX / Channel Output
    channel_out,
    # Control Scope
    set_control_scope,
    # Virtual LJ
    virtual_lj,
    virtual_lj_fx,
)


def _fake_client():
    """Return a MagicMock that simulates BeyondClient."""
    fake = MagicMock()
    fake.send_osc.return_value = {
        "address": "/test",
        "values": [],
        "type_tags": "",
        "host": "127.0.0.1",
        "port": 12000,
        "bytes_sent": 16,
    }
    fake.health_check.return_value = {
        "reachable": True,
        "host": "127.0.0.1",
        "port": 12000,
        "elapsed_ms": 0.5,
    }
    fake.send_bundle.return_value = {
        "bundle": True,
        "message_count": 1,
        "messages": [{"address": "/test", "values": []}],
        "host": "127.0.0.1",
        "port": 12000,
        "bytes_sent": 32,
    }
    return fake


# ================================================================
# System
# ================================================================


def test_get_server_config():
    payload = json.loads(get_server_config())
    assert payload["host"] == "127.0.0.1"
    assert payload["osc_port"] == 12000
    assert "target" in payload
    assert "allowed_hosts" in payload
    assert payload["safety_profile"] == "lab"
    assert "read_only" in payload
    assert "confirm_destructive" in payload


@patch("beyond_mcp.server._client")
def test_health_check(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    payload = json.loads(health_check())
    assert payload["reachable"] is True
    assert payload["host"] == "127.0.0.1"
    fake.health_check.assert_called_once()


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


def test_send_osc_raw_destructive_requires_confirm():
    os.environ["BEYOND_CONFIRM_DESTRUCTIVE"] = "1"
    try:
        payload = json.loads(send_osc_raw("/beyond/general/BlackOut", "[]"))
        assert payload["ok"] is False
        assert "confirm=true" in payload["error"]
    finally:
        os.environ.pop("BEYOND_CONFIRM_DESTRUCTIVE", None)


@patch("beyond_mcp.server._client")
def test_send_osc_raw_destructive_with_confirm(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    os.environ["BEYOND_CONFIRM_DESTRUCTIVE"] = "1"
    try:
        payload = json.loads(send_osc_raw("/beyond/general/BlackOut", "[]", confirm=True))
        assert payload["address"] == "/test"
        fake.send_osc.assert_called_once()
    finally:
        os.environ.pop("BEYOND_CONFIRM_DESTRUCTIVE", None)


@patch("beyond_mcp.server._client")
def test_send_osc_raw_with_type_tags(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    send_osc_raw("/test", "[1]", type_tags="i")
    fake.send_osc.assert_called_once_with("/test", [1], type_tags="i")


@patch("beyond_mcp.server._client")
def test_send_osc_bundle_valid(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    msg = '[["/beyond/general/BlackOut", []], ["/beyond/general/SetBpm", [120]]]'
    payload = json.loads(send_osc_bundle(msg))
    assert payload["bundle"] is True
    fake.send_bundle.assert_called_once()
    args = fake.send_bundle.call_args[0][0]
    assert args == [("/beyond/general/BlackOut", []), ("/beyond/general/SetBpm", [120])]


@patch("beyond_mcp.server._client")
def test_send_osc_bundle_with_timetag(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    msg = '[["/beyond/general/SetBpm", [120]]]'
    json.loads(send_osc_bundle(msg, timetag=99))
    fake.send_bundle.assert_called_once_with([("/beyond/general/SetBpm", [120])], timetag=99)


def test_send_osc_bundle_invalid_json():
    payload = json.loads(send_osc_bundle("not json"))
    assert payload["ok"] is False
    assert "Invalid JSON" in payload["error"]


def test_send_osc_bundle_not_array():
    payload = json.loads(send_osc_bundle('{"a": 1}'))
    assert payload["ok"] is False
    assert "JSON array" in payload["error"]


def test_send_osc_bundle_bad_entry_not_list():
    payload = json.loads(send_osc_bundle('[42]'))
    assert payload["ok"] is False
    assert "Entry 0" in payload["error"]


def test_send_osc_bundle_bad_entry_wrong_length():
    payload = json.loads(send_osc_bundle('[["/test"]]'))
    assert payload["ok"] is False
    assert "Entry 0" in payload["error"]


def test_send_osc_bundle_bad_entry_types():
    payload = json.loads(send_osc_bundle('[[123, []]]'))
    assert payload["ok"] is False
    assert "Entry 0" in payload["error"]


def test_send_osc_bundle_bad_values_type():
    payload = json.loads(send_osc_bundle('[["/test", "not_array"]]'))
    assert payload["ok"] is False
    assert "Entry 0" in payload["error"]


def test_send_osc_bundle_destructive_requires_confirm():
    os.environ["BEYOND_CONFIRM_DESTRUCTIVE"] = "1"
    try:
        payload = json.loads(send_osc_bundle('[["/beyond/general/BlackOut", []]]'))
        assert payload["ok"] is False
        assert "confirm=true" in payload["error"]
    finally:
        os.environ.pop("BEYOND_CONFIRM_DESTRUCTIVE", None)


@patch("beyond_mcp.server._client")
def test_send_osc_bundle_destructive_with_confirm(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    os.environ["BEYOND_CONFIRM_DESTRUCTIVE"] = "1"
    try:
        payload = json.loads(send_osc_bundle('[["/beyond/general/BlackOut", []]]', confirm=True))
        assert payload["bundle"] is True
        fake.send_bundle.assert_called_once()
    finally:
        os.environ.pop("BEYOND_CONFIRM_DESTRUCTIVE", None)


def test_preview_osc():
    payload = json.loads(preview_osc("/beyond/general/BlackOut", "[]"))
    assert payload["preview"] is True
    assert payload["address"] == "/beyond/general/BlackOut"
    assert payload["packet_bytes"] > 0
    assert "No OSC message was sent" in payload["note"]


def test_preview_osc_bundle():
    payload = json.loads(preview_osc_bundle('[["/beyond/general/SetBpm", [120]]]'))
    assert payload["preview"] is True
    assert payload["bundle"] is True
    assert payload["message_count"] == 1
    assert payload["packet_bytes"] > 0


def test_preview_osc_with_values():
    payload = json.loads(preview_osc("/beyond/master/livecontrol/brightness", "[75.0]"))
    assert payload["preview"] is True
    assert payload["values"] == [75.0]


def test_preview_osc_with_type_tags():
    payload = json.loads(preview_osc("/test", "[1]", type_tags="i"))
    assert payload["preview"] is True
    assert payload["type_tags"] == "i"


def test_preview_osc_invalid_json():
    payload = json.loads(preview_osc("/test", "bad"))
    assert payload["ok"] is False


def test_preview_osc_non_array():
    payload = json.loads(preview_osc("/test", '{"a":1}'))
    assert payload["ok"] is False


# ================================================================
# Master Controls
# ================================================================


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


@patch("beyond_mcp.server._client")
def test_set_master_brightness_boundary_zero(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    set_master_brightness(0.0)
    fake.send_osc.assert_called_once()


@patch("beyond_mcp.server._client")
def test_set_master_brightness_boundary_hundred(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    set_master_brightness(100.0)
    fake.send_osc.assert_called_once()


def test_set_master_brightness_out_of_range_high():
    payload = json.loads(set_master_brightness(150.0))
    assert payload["ok"] is False


def test_set_master_brightness_out_of_range_low():
    payload = json.loads(set_master_brightness(-1.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_blackout(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(blackout())
    fake.send_osc.assert_called_once_with("/beyond/general/BlackOut", [])


@patch("beyond_mcp.server._client")
def test_enable_laser_output(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(enable_laser_output())
    fake.send_osc.assert_called_once_with("/beyond/general/EnableLaserOutput", [])


@patch("beyond_mcp.server._client")
def test_disable_laser_output(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(disable_laser_output())
    fake.send_osc.assert_called_once_with("/beyond/general/DisableLaserOutput", [])


@patch("beyond_mcp.server._client")
def test_master_pause(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(master_pause(1))
    fake.send_osc.assert_called_once_with("/beyond/general/MasterPause", [1])


@patch("beyond_mcp.server._client")
def test_master_pause_zero(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(master_pause(0))
    fake.send_osc.assert_called_once_with("/beyond/general/MasterPause", [0])


def test_master_pause_invalid_value():
    payload = json.loads(master_pause(2))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_master_pause_time(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(master_pause_time(1))
    fake.send_osc.assert_called_once_with("/beyond/general/MasterPauseTime", [1])


@patch("beyond_mcp.server._client")
def test_master_pause_time_zero(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(master_pause_time(0))
    fake.send_osc.assert_called_once_with("/beyond/general/MasterPauseTime", [0])


def test_master_pause_time_invalid_value():
    payload = json.loads(master_pause_time(5))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_set_master_speed(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_master_speed(2.0))
    fake.send_osc.assert_called_once_with("/beyond/general/MasterSpeed", [2.0])


def test_set_master_speed_out_of_range():
    payload = json.loads(set_master_speed(15.0))
    assert payload["ok"] is False


def test_set_master_speed_negative():
    payload = json.loads(set_master_speed(-1.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_stop_all_now(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(stop_all_now())
    fake.send_osc.assert_called_once_with("/beyond/general/StopAllNow", [])


@patch("beyond_mcp.server._client")
def test_stop_all_sync(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(stop_all_sync(1.5))
    fake.send_osc.assert_called_once_with("/beyond/general/StopAllSync", [1.5])


@patch("beyond_mcp.server._client")
def test_stop_all_sync_default_fade(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(stop_all_sync())
    fake.send_osc.assert_called_once_with("/beyond/general/StopAllSync", [0.0])


def test_stop_all_sync_negative_fade():
    payload = json.loads(stop_all_sync(-1.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_stop_all_async(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(stop_all_async(2.0))
    fake.send_osc.assert_called_once_with("/beyond/general/StopAllAsync", [2.0])


@patch("beyond_mcp.server._client")
def test_stop_all_async_default_fade(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(stop_all_async())
    fake.send_osc.assert_called_once_with("/beyond/general/StopAllAsync", [0.0])


def test_stop_all_async_negative_fade():
    payload = json.loads(stop_all_async(-0.5))
    assert payload["ok"] is False


# ================================================================
# BPM / Beat
# ================================================================


@patch("beyond_mcp.server._client")
def test_set_bpm(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_bpm(128.0))
    fake.send_osc.assert_called_once_with("/beyond/general/SetBpm", [128.0])


@patch("beyond_mcp.server._client")
def test_set_bpm_boundary_low(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_bpm(1.0))
    fake.send_osc.assert_called_once()


@patch("beyond_mcp.server._client")
def test_set_bpm_boundary_high(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_bpm(999.0))
    fake.send_osc.assert_called_once()


def test_set_bpm_out_of_range_zero():
    payload = json.loads(set_bpm(0.0))
    assert payload["ok"] is False


def test_set_bpm_out_of_range_high():
    payload = json.loads(set_bpm(1000.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_set_bpm_delta(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_bpm_delta(5.0))
    fake.send_osc.assert_called_once_with("/beyond/general/SetBpmDelta", [5.0])


@patch("beyond_mcp.server._client")
def test_set_bpm_delta_negative(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_bpm_delta(-10.0))
    fake.send_osc.assert_called_once_with("/beyond/general/SetBpmDelta", [-10.0])


@patch("beyond_mcp.server._client")
def test_beat_tap(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(beat_tap())
    fake.send_osc.assert_called_once_with("/beyond/general/BeatTap", [])


@patch("beyond_mcp.server._client")
def test_beat_resync(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(beat_resync())
    fake.send_osc.assert_called_once_with("/beyond/general/BeatResync", [])


@patch("beyond_mcp.server._client")
def test_beat_source_timer(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(beat_source_timer())
    fake.send_osc.assert_called_once_with("/beyond/general/TimerBeat", [])


@patch("beyond_mcp.server._client")
def test_beat_source_audio(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(beat_source_audio())
    fake.send_osc.assert_called_once_with("/beyond/general/AudioBeat", [])


@patch("beyond_mcp.server._client")
def test_beat_source_manual(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(beat_source_manual())
    fake.send_osc.assert_called_once_with("/beyond/general/ManualBeat", [])


# ================================================================
# Cue Mode
# ================================================================


@patch("beyond_mcp.server._client")
def test_set_cue_mode_single(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_cue_mode_single())
    fake.send_osc.assert_called_once_with("/beyond/general/OneCue", [])


@patch("beyond_mcp.server._client")
def test_set_cue_mode_one_per(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_cue_mode_one_per())
    fake.send_osc.assert_called_once_with("/beyond/general/OnePer", [])


@patch("beyond_mcp.server._client")
def test_set_cue_mode_multi(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_cue_mode_multi())
    fake.send_osc.assert_called_once_with("/beyond/general/MultiCue", [])


# ================================================================
# Click Behavior
# ================================================================


@patch("beyond_mcp.server._client")
def test_click_mode_select(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(click_mode_select())
    fake.send_osc.assert_called_once_with("/beyond/general/ClickSelect", [])


@patch("beyond_mcp.server._client")
def test_click_mode_toggle(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(click_mode_toggle())
    fake.send_osc.assert_called_once_with("/beyond/general/ClickToggle", [])


@patch("beyond_mcp.server._client")
def test_click_mode_restart(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(click_mode_restart())
    fake.send_osc.assert_called_once_with("/beyond/general/ClickRestart", [])


@patch("beyond_mcp.server._client")
def test_click_mode_flash(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(click_mode_flash())
    fake.send_osc.assert_called_once_with("/beyond/general/ClickFlash", [])


@patch("beyond_mcp.server._client")
def test_click_mode_solo_flash(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(click_mode_solo_flash())
    fake.send_osc.assert_called_once_with("/beyond/general/ClickSoloFlash", [])


@patch("beyond_mcp.server._client")
def test_click_mode_live(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(click_mode_live())
    fake.send_osc.assert_called_once_with("/beyond/general/ClickLive", [])


@patch("beyond_mcp.server._client")
def test_set_click_scroll_zoom(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_click_scroll("zoom", 50.0))
    fake.send_osc.assert_called_once_with("/beyond/general/ClickScrollZoom", [50.0])


@patch("beyond_mcp.server._client")
def test_set_click_scroll_size(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_click_scroll("size", 10.0))
    fake.send_osc.assert_called_once_with("/beyond/general/ClickScrollSize", [10.0])


@patch("beyond_mcp.server._client")
def test_set_click_scroll_fade(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_click_scroll("fade", 5.0))
    fake.send_osc.assert_called_once_with("/beyond/general/ClickScrollFade", [5.0])


@patch("beyond_mcp.server._client")
def test_set_click_scroll_vpoints(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_click_scroll("vpoints", 80.0))
    fake.send_osc.assert_called_once_with("/beyond/general/ClickScrollVPoints", [80.0])


@patch("beyond_mcp.server._client")
def test_set_click_scroll_scanrate(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_click_scroll("scanrate", 100.0))
    fake.send_osc.assert_called_once_with("/beyond/general/ClickScrollScanRate", [100.0])


@patch("beyond_mcp.server._client")
def test_set_click_scroll_color(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_click_scroll("color", 200.0))
    fake.send_osc.assert_called_once_with("/beyond/general/ClickScrollColor", [200.0])


@patch("beyond_mcp.server._client")
def test_set_click_scroll_anispeed(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_click_scroll("anispeed", 150.0))
    fake.send_osc.assert_called_once_with("/beyond/general/ClickScrollAniSpeed", [150.0])


@patch("beyond_mcp.server._client")
def test_set_click_scroll_red(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_click_scroll("red", 128.0))
    fake.send_osc.assert_called_once_with("/beyond/general/ClickScrollR", [128.0])


@patch("beyond_mcp.server._client")
def test_set_click_scroll_green(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_click_scroll("green", 64.0))
    fake.send_osc.assert_called_once_with("/beyond/general/ClickScrollG", [64.0])


@patch("beyond_mcp.server._client")
def test_set_click_scroll_blue(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_click_scroll("blue", 255.0))
    fake.send_osc.assert_called_once_with("/beyond/general/ClickScrollB", [255.0])


@patch("beyond_mcp.server._client")
def test_set_click_scroll_alpha(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_click_scroll("alpha", 200.0))
    fake.send_osc.assert_called_once_with("/beyond/general/ClickScrollA", [200.0])


def test_set_click_scroll_invalid_parameter():
    payload = json.loads(set_click_scroll("invalid_param", 1.0))
    assert payload["ok"] is False
    assert "must be one of" in payload["error"]


# ================================================================
# Transitions
# ================================================================


@patch("beyond_mcp.server._client")
def test_set_transition_type(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_transition_type(3))
    fake.send_osc.assert_called_once_with("/beyond/general/Transition", [3])


@patch("beyond_mcp.server._client")
def test_set_master_transition_index(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_master_transition_index(2))
    fake.send_osc.assert_called_once_with("/beyond/general/MasterTransitionIndex", [2])


@patch("beyond_mcp.server._client")
def test_set_master_transition_time(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_master_transition_time(1.5))
    fake.send_osc.assert_called_once_with("/beyond/general/MasterTransitionTime", [1.5])


@patch("beyond_mcp.server._client")
def test_set_master_transition_time_zero(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_master_transition_time(0.0))
    fake.send_osc.assert_called_once()


def test_set_master_transition_time_negative():
    payload = json.loads(set_master_transition_time(-1.0))
    assert payload["ok"] is False


# ================================================================
# Cue / Cell Control
# ================================================================


@patch("beyond_mcp.server._client")
def test_select_cue(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(select_cue("my_cue"))
    fake.send_osc.assert_called_once_with("/beyond/general/SelectCue", ["my_cue"])


@patch("beyond_mcp.server._client")
def test_start_cue_by_name(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(start_cue_by_name("intro_beam"))
    fake.send_osc.assert_called_once_with("/beyond/general/StartCue", ["intro_beam"])


@patch("beyond_mcp.server._client")
def test_stop_cue_by_name(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(stop_cue_by_name("intro_beam"))
    fake.send_osc.assert_called_once_with("/beyond/general/StopCue", ["intro_beam"])


@patch("beyond_mcp.server._client")
def test_stop_cue_now(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(stop_cue_now(1, 3))
    fake.send_osc.assert_called_once_with("/beyond/general/StopCueNow", [1, 3])


@patch("beyond_mcp.server._client")
def test_stop_cue_sync(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(stop_cue_sync(1, 2, 0.5))
    fake.send_osc.assert_called_once_with("/beyond/general/StopCueSync", [1, 2, 0.5])


@patch("beyond_mcp.server._client")
def test_stop_cue_sync_default_fade(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(stop_cue_sync(0, 0))
    fake.send_osc.assert_called_once_with("/beyond/general/StopCueSync", [0, 0, 0.0])


def test_stop_cue_sync_negative_fade():
    payload = json.loads(stop_cue_sync(1, 2, -1.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_cue_down(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(cue_down(0, 1, 3))
    fake.send_osc.assert_called_once_with("/beyond/general/CueDown", [0, 1, 3])


@patch("beyond_mcp.server._client")
def test_cue_down_default_count(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(cue_down(0, 1))
    fake.send_osc.assert_called_once_with("/beyond/general/CueDown", [0, 1, 1])


@patch("beyond_mcp.server._client")
def test_cue_up(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(cue_up(0, 5, 2))
    fake.send_osc.assert_called_once_with("/beyond/general/CueUp", [0, 5, 2])


@patch("beyond_mcp.server._client")
def test_cue_up_default_count(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(cue_up(0, 5))
    fake.send_osc.assert_called_once_with("/beyond/general/CueUp", [0, 5, 1])


@patch("beyond_mcp.server._client")
def test_pause_cue(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(pause_cue(1, 2, 1))
    fake.send_osc.assert_called_once_with("/beyond/general/PauseCue", [1, 2, 1])


@patch("beyond_mcp.server._client")
def test_pause_cue_unpause(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(pause_cue(1, 2, 0))
    fake.send_osc.assert_called_once_with("/beyond/general/PauseCue", [1, 2, 0])


def test_pause_cue_invalid_state():
    payload = json.loads(pause_cue(1, 2, 3))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_restart_cue(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(restart_cue(0, 4))
    fake.send_osc.assert_called_once_with("/beyond/general/RestartCue", [0, 4])


@patch("beyond_mcp.server._client")
def test_focus_cell(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(focus_cell(0, 7))
    fake.send_osc.assert_called_once_with("/beyond/general/FocusCell", [0, 7])


@patch("beyond_mcp.server._client")
def test_focus_cell_index(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(focus_cell_index(15))
    fake.send_osc.assert_called_once_with("/beyond/general/FocusCellIndex", [15])


@patch("beyond_mcp.server._client")
def test_start_cell(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(start_cell())
    fake.send_osc.assert_called_once_with("/beyond/general/StartCell", [])


@patch("beyond_mcp.server._client")
def test_restart_cell(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(restart_cell())
    fake.send_osc.assert_called_once_with("/beyond/general/ReStartCell", [])


@patch("beyond_mcp.server._client")
def test_stop_cell(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(stop_cell())
    fake.send_osc.assert_called_once_with("/beyond/general/StopCell", [])


@patch("beyond_mcp.server._client")
def test_shift_focus(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(shift_focus(2))
    fake.send_osc.assert_called_once_with("/beyond/general/ShiftFocus", [2])


@patch("beyond_mcp.server._client")
def test_shift_focus_negative(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(shift_focus(-1))
    fake.send_osc.assert_called_once_with("/beyond/general/ShiftFocus", [-1])


@patch("beyond_mcp.server._client")
def test_move_focus(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(move_focus(1, -1))
    fake.send_osc.assert_called_once_with("/beyond/general/MoveFocus", [1, -1])


@patch("beyond_mcp.server._client")
def test_unselect_all_cues(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(unselect_all_cues())
    fake.send_osc.assert_called_once_with("/beyond/general/UnselectAllCue", [])


# ================================================================
# Workspace
# ================================================================


@patch("beyond_mcp.server._client")
def test_load_cue(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(load_cue("my_cue"))
    fake.send_osc.assert_called_once_with("/beyond/general/LoadCue", ["my_cue"])


@patch("beyond_mcp.server._client")
def test_load_workspace(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(load_workspace("show_v2"))
    fake.send_osc.assert_called_once_with("/beyond/general/LoadWorkspace", ["show_v2"])


def test_load_workspace_requires_confirm():
    payload = _with_confirm_destructive(load_workspace, "show_v2")
    assert payload["ok"] is False
    assert "confirm=true" in payload["error"]


# ================================================================
# Page / Tab / Category Navigation
# ================================================================


@patch("beyond_mcp.server._client")
def test_select_page(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(select_page(3))
    fake.send_osc.assert_called_once_with("/beyond/general/SelectPage", [3])


def test_select_page_negative_rejected():
    payload = json.loads(select_page(-1))
    assert payload["ok"] is False
    assert "page_index must be >=" in payload["error"]


@patch("beyond_mcp.server._client")
def test_select_next_page(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(select_next_page())
    fake.send_osc.assert_called_once_with("/beyond/general/SelectNextPage", [])


@patch("beyond_mcp.server._client")
def test_select_prev_page(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(select_prev_page())
    fake.send_osc.assert_called_once_with("/beyond/general/SelectPrevPage", [])


@patch("beyond_mcp.server._client")
def test_select_tab(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(select_tab(2))
    fake.send_osc.assert_called_once_with("/beyond/general/SelectTab", [2])


def test_select_tab_negative_rejected():
    payload = json.loads(select_tab(-1))
    assert payload["ok"] is False
    assert "tab_index must be >=" in payload["error"]


@patch("beyond_mcp.server._client")
def test_select_tab_by_name(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(select_tab_by_name("effects"))
    fake.send_osc.assert_called_once_with("/beyond/general/SelectTabName", ["effects"])


@patch("beyond_mcp.server._client")
def test_select_next_tab(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(select_next_tab())
    fake.send_osc.assert_called_once_with("/beyond/general/SelectNextTab", [])


@patch("beyond_mcp.server._client")
def test_select_prev_tab(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(select_prev_tab())
    fake.send_osc.assert_called_once_with("/beyond/general/SelectPrevTab", [])


@patch("beyond_mcp.server._client")
def test_select_all_categories(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(select_all_categories())
    fake.send_osc.assert_called_once_with("/beyond/general/SelectAllCat", [])


@patch("beyond_mcp.server._client")
def test_select_category(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(select_category(5))
    fake.send_osc.assert_called_once_with("/beyond/general/SelectCat", [5])


def test_select_category_negative_rejected():
    payload = json.loads(select_category(-1))
    assert payload["ok"] is False
    assert "index must be >=" in payload["error"]


@patch("beyond_mcp.server._client")
def test_select_category_by_name(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(select_category_by_name("beams"))
    fake.send_osc.assert_called_once_with("/beyond/general/SelectCatName", ["beams"])


@patch("beyond_mcp.server._client")
def test_select_next_category(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(select_next_category())
    fake.send_osc.assert_called_once_with("/beyond/general/SelectNextCat", [])


@patch("beyond_mcp.server._client")
def test_select_prev_category(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(select_prev_category())
    fake.send_osc.assert_called_once_with("/beyond/general/SelectPrevCat", [])


# ================================================================
# Grid Management
# ================================================================


@patch("beyond_mcp.server._client")
def test_set_grid_size(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_grid_size(10, 8))
    fake.send_osc.assert_called_once_with("/beyond/general/SetGridSize", [10, 8])


@patch("beyond_mcp.server._client")
def test_select_grid(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(select_grid(2))
    fake.send_osc.assert_called_once_with("/beyond/general/SelectGrid", [2])


def test_select_grid_negative_rejected():
    payload = json.loads(select_grid(-1))
    assert payload["ok"] is False
    assert "index must be >=" in payload["error"]


# ================================================================
# Zone Control
# ================================================================


@patch("beyond_mcp.server._client")
def test_mute_zone(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(mute_zone(1))
    fake.send_osc.assert_called_once_with("/beyond/general/MuteZone", [1])


def test_mute_zone_negative_rejected():
    payload = json.loads(mute_zone(-1))
    assert payload["ok"] is False
    assert "zone_index must be >=" in payload["error"]


@patch("beyond_mcp.server._client")
def test_unmute_zone(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(unmute_zone(1))
    fake.send_osc.assert_called_once_with("/beyond/general/UnmuteZone", [1])


def test_unmute_zone_negative_rejected():
    payload = json.loads(unmute_zone(-1))
    assert payload["ok"] is False
    assert "zone_index must be >=" in payload["error"]


@patch("beyond_mcp.server._client")
def test_toggle_mute_zone(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(toggle_mute_zone(3))
    fake.send_osc.assert_called_once_with("/beyond/general/ToggleMuteZone", [3])


def test_toggle_mute_zone_negative_rejected():
    payload = json.loads(toggle_mute_zone(-1))
    assert payload["ok"] is False
    assert "zone_index must be >=" in payload["error"]


@patch("beyond_mcp.server._client")
def test_unmute_all_zones(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(unmute_all_zones())
    fake.send_osc.assert_called_once_with("/beyond/general/UnmuteAllZone", [])


@patch("beyond_mcp.server._client")
def test_stop_zone(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(stop_zone(2, 0.5))
    fake.send_osc.assert_called_once_with("/beyond/general/StopZone", [2, 0.5])


@patch("beyond_mcp.server._client")
def test_stop_zone_default_fade(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(stop_zone(2))
    fake.send_osc.assert_called_once_with("/beyond/general/StopZone", [2, 0.0])


def test_stop_zone_negative_fade():
    payload = json.loads(stop_zone(2, -1.0))
    assert payload["ok"] is False


def test_stop_zone_requires_confirm():
    payload = _with_confirm_destructive(stop_zone, 2, 0.0)
    assert payload["ok"] is False
    assert "confirm=true" in payload["error"]


@patch("beyond_mcp.server._client")
def test_stop_zone_with_confirm(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    os.environ["BEYOND_CONFIRM_DESTRUCTIVE"] = "1"
    try:
        json.loads(stop_zone(2, 0.0, confirm=True))
        fake.send_osc.assert_called_once()
    finally:
        os.environ.pop("BEYOND_CONFIRM_DESTRUCTIVE", None)


@patch("beyond_mcp.server._client")
def test_stop_zone_by_name(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(stop_zone_by_name("main_zone"))
    fake.send_osc.assert_called_once_with("/beyond/general/StopZoneByName", ["main_zone"])


@patch("beyond_mcp.server._client")
def test_stop_zones_of_projector(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(stop_zones_of_projector(0))
    fake.send_osc.assert_called_once_with("/beyond/general/StopZonesOfProjector", [0])


@patch("beyond_mcp.server._client")
def test_stop_projector_by_name(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(stop_projector_by_name("proj_a"))
    fake.send_osc.assert_called_once_with("/beyond/general/StopProjectorByName", ["proj_a"])


def test_stop_projector_by_name_requires_confirm():
    payload = _with_confirm_destructive(stop_projector_by_name, "proj_a")
    assert payload["ok"] is False
    assert "confirm=true" in payload["error"]


@patch("beyond_mcp.server._client")
def test_select_zone(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(select_zone(4))
    fake.send_osc.assert_called_once_with("/beyond/general/SelectZone", [4])


def test_select_zone_negative_rejected():
    payload = json.loads(select_zone(-1))
    assert payload["ok"] is False
    assert "zone_index must be >=" in payload["error"]


@patch("beyond_mcp.server._client")
def test_select_zone_by_name(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(select_zone_by_name("zone_a"))
    fake.send_osc.assert_called_once_with("/beyond/general/SelectZoneName", ["zone_a"])


@patch("beyond_mcp.server._client")
def test_unselect_zone(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(unselect_zone(2))
    fake.send_osc.assert_called_once_with("/beyond/general/UnSelectZone", [2])


def test_unselect_zone_negative_rejected():
    payload = json.loads(unselect_zone(-1))
    assert payload["ok"] is False
    assert "zone_index must be >=" in payload["error"]


@patch("beyond_mcp.server._client")
def test_unselect_all_zones(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(unselect_all_zones())
    fake.send_osc.assert_called_once_with("/beyond/general/UnselectAllZones", [])


@patch("beyond_mcp.server._client")
def test_toggle_select_zone(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(toggle_select_zone(1))
    fake.send_osc.assert_called_once_with("/beyond/general/ToggleSelectZone", [1])


def test_toggle_select_zone_negative_rejected():
    payload = json.loads(toggle_select_zone(-1))
    assert payload["ok"] is False
    assert "zone_index must be >=" in payload["error"]


@patch("beyond_mcp.server._client")
def test_store_zone_selection(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(store_zone_selection())
    fake.send_osc.assert_called_once_with("/beyond/general/StoreZoneSelection", [])


@patch("beyond_mcp.server._client")
def test_restore_zone_selection(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(restore_zone_selection())
    fake.send_osc.assert_called_once_with("/beyond/general/ReStoreZoneSelection", [])


@patch("beyond_mcp.server._client")
def test_set_zone_brightness(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_zone_brightness(3, 80.0))
    fake.send_osc.assert_called_once_with(
        "/beyond/zone/3/livecontrol/brightness", [80.0]
    )


def test_set_zone_brightness_out_of_range():
    payload = json.loads(set_zone_brightness(1, 110.0))
    assert payload["ok"] is False


def test_set_zone_brightness_negative():
    payload = json.loads(set_zone_brightness(1, -5.0))
    assert payload["ok"] is False


# ================================================================
# Live Control Parameters (Master scope)
# ================================================================


@patch("beyond_mcp.server._client")
def test_set_master_size(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_master_size(50.0, 50.0))
    fake.send_osc.assert_called_once_with(
        "/beyond/master/livecontrol/size", [50.0, 50.0]
    )


def test_set_master_size_out_of_range():
    payload = json.loads(set_master_size(500.0, 0.0))
    assert payload["ok"] is False


def test_set_master_size_out_of_range_negative():
    payload = json.loads(set_master_size(0.0, -500.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_set_master_position(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_master_position(100.0, -200.0))
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
    json.loads(set_master_rotation(45.0, 0.0, 90.0))
    fake.send_osc.assert_called_once_with(
        "/beyond/master/livecontrol/angle", [45.0, 0.0, 90.0]
    )


def test_set_master_rotation_out_of_range():
    payload = json.loads(set_master_rotation(3000.0, 0.0, 0.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_set_master_rotation_speed(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_master_rotation_speed(100.0, -50.0, 0.0))
    fake.send_osc.assert_called_once_with(
        "/beyond/master/livecontrol/roto", [100.0, -50.0, 0.0]
    )


def test_set_master_rotation_speed_out_of_range():
    payload = json.loads(set_master_rotation_speed(1500.0, 0.0, 0.0))
    assert payload["ok"] is False


def test_set_master_rotation_speed_out_of_range_negative():
    payload = json.loads(set_master_rotation_speed(0.0, -1500.0, 0.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_set_master_color(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_master_color(255.0, 128.0, 0.0))
    assert fake.send_osc.call_count == 3
    calls = fake.send_osc.call_args_list
    assert calls[0].args == ("/beyond/master/livecontrol/red", [255.0])
    assert calls[1].args == ("/beyond/master/livecontrol/green", [128.0])
    assert calls[2].args == ("/beyond/master/livecontrol/blue", [0.0])


def test_set_master_color_out_of_range():
    payload = json.loads(set_master_color(300.0, 0.0, 0.0))
    assert payload["ok"] is False


def test_set_master_color_negative():
    payload = json.loads(set_master_color(-1.0, 0.0, 0.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_set_master_alpha(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_master_alpha(200.0))
    fake.send_osc.assert_called_once_with(
        "/beyond/master/livecontrol/alpha", [200.0]
    )


def test_set_master_alpha_out_of_range():
    payload = json.loads(set_master_alpha(256.0))
    assert payload["ok"] is False


def test_set_master_alpha_negative():
    payload = json.loads(set_master_alpha(-1.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_set_master_zoom(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_master_zoom(50.0))
    fake.send_osc.assert_called_once_with(
        "/beyond/master/livecontrol/zoom", [50.0]
    )


def test_set_master_zoom_out_of_range():
    payload = json.loads(set_master_zoom(150.0))
    assert payload["ok"] is False


def test_set_master_zoom_negative():
    payload = json.loads(set_master_zoom(-1.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_set_master_scan_rate(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_master_scan_rate(30.0))
    fake.send_osc.assert_called_once_with(
        "/beyond/master/livecontrol/scanrate", [30.0]
    )


def test_set_master_scan_rate_out_of_range_low():
    payload = json.loads(set_master_scan_rate(5.0))
    assert payload["ok"] is False


def test_set_master_scan_rate_out_of_range_high():
    payload = json.loads(set_master_scan_rate(250.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_set_master_visible_points(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_master_visible_points(75.0))
    fake.send_osc.assert_called_once_with(
        "/beyond/master/livecontrol/visiblepoints", [75.0]
    )


def test_set_master_visible_points_out_of_range():
    payload = json.loads(set_master_visible_points(101.0))
    assert payload["ok"] is False


def test_set_master_visible_points_negative():
    payload = json.loads(set_master_visible_points(-1.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_set_master_color_slider(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_master_color_slider(128.0))
    fake.send_osc.assert_called_once_with(
        "/beyond/master/livecontrol/colorslider", [128.0]
    )


def test_set_master_color_slider_out_of_range():
    payload = json.loads(set_master_color_slider(256.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_set_master_animation_speed(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_master_animation_speed(200.0))
    fake.send_osc.assert_called_once_with(
        "/beyond/master/livecontrol/anispeed", [200.0]
    )


def test_set_master_animation_speed_out_of_range():
    payload = json.loads(set_master_animation_speed(401.0))
    assert payload["ok"] is False


def test_set_master_animation_speed_negative():
    payload = json.loads(set_master_animation_speed(-1.0))
    assert payload["ok"] is False


# ================================================================
# Live Control: Effects (Master scope)
# ================================================================


@patch("beyond_mcp.server._client")
def test_set_master_effect(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_master_effect(1, 10))
    fake.send_osc.assert_called_once_with("/beyond/master/livecontrol/fx1", [10.0])


@patch("beyond_mcp.server._client")
def test_set_master_effect_stop(mock_client):
    """effect_index -1 means stop the effect."""
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_master_effect(2, -1))
    fake.send_osc.assert_called_once_with("/beyond/master/livecontrol/fx2", [-1.0])


def test_set_master_effect_invalid_slot():
    payload = json.loads(set_master_effect(5, 10))
    assert payload["ok"] is False


def test_set_master_effect_index_out_of_range():
    payload = json.loads(set_master_effect(1, 48))
    assert payload["ok"] is False


def test_set_master_effect_index_too_low():
    payload = json.loads(set_master_effect(1, -2))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_set_master_effect_action(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_master_effect_action(3, 75.0))
    fake.send_osc.assert_called_once_with("/beyond/master/livecontrol/fx3action", [75.0])


def test_set_master_effect_action_invalid_slot():
    payload = json.loads(set_master_effect_action(0, 50.0))
    assert payload["ok"] is False


def test_set_master_effect_action_out_of_range():
    payload = json.loads(set_master_effect_action(1, 101.0))
    assert payload["ok"] is False


def test_set_master_effect_action_negative():
    payload = json.loads(set_master_effect_action(1, -1.0))
    assert payload["ok"] is False


# ================================================================
# Projector Control
# ================================================================


@patch("beyond_mcp.server._client")
def test_set_projector_size(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_projector_size(0, 50.0, 75.0))
    assert fake.send_osc.call_count == 2
    calls = fake.send_osc.call_args_list
    assert calls[0].args == ("/beyond/projector/0/sizex", [50.0])
    assert calls[1].args == ("/beyond/projector/0/sizey", [75.0])


def test_set_projector_size_out_of_range():
    payload = json.loads(set_projector_size(0, 200.0, 0.0))
    assert payload["ok"] is False


def test_set_projector_size_out_of_range_negative():
    payload = json.loads(set_projector_size(0, 0.0, -200.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_set_projector_position(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_projector_position(1, -10.0, 20.0))
    assert fake.send_osc.call_count == 2
    calls = fake.send_osc.call_args_list
    assert calls[0].args == ("/beyond/projector/1/posx", [-10.0])
    assert calls[1].args == ("/beyond/projector/1/posy", [20.0])


def test_set_projector_position_out_of_range():
    payload = json.loads(set_projector_position(0, 150.0, 0.0))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_projector_swap_xy(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(projector_swap_xy(0, 1))
    fake.send_osc.assert_called_once_with("/beyond/projector/0/swapxy", [1.0])


@patch("beyond_mcp.server._client")
def test_projector_swap_xy_toggle(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(projector_swap_xy(0, 2))
    fake.send_osc.assert_called_once_with("/beyond/projector/0/swapxy", [2.0])


def test_projector_swap_xy_invalid_state():
    payload = json.loads(projector_swap_xy(0, 3))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_projector_invert_x(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(projector_invert_x(1, 1))
    fake.send_osc.assert_called_once_with("/beyond/projector/1/invx", [1.0])


@patch("beyond_mcp.server._client")
def test_projector_invert_x_off(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(projector_invert_x(1, 0))
    fake.send_osc.assert_called_once_with("/beyond/projector/1/invx", [0.0])


def test_projector_invert_x_invalid_state():
    payload = json.loads(projector_invert_x(0, 5))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_projector_invert_y(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(projector_invert_y(0, 2))
    fake.send_osc.assert_called_once_with("/beyond/projector/0/invy", [2.0])


def test_projector_invert_y_invalid_state():
    payload = json.loads(projector_invert_y(0, 4))
    assert payload["ok"] is False


# ================================================================
# Zone Setup / Geometric Correction
# ================================================================


@patch("beyond_mcp.server._client")
def test_zone_setup_select(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(zone_setup_select(3))
    fake.send_osc.assert_called_once_with("/beyond/zonesetup/zone", [3.0])


@patch("beyond_mcp.server._client")
def test_zone_setup_next_zone(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(zone_setup_next_zone())
    fake.send_osc.assert_called_once_with("/beyond/zonesetup/nextzone", [])


@patch("beyond_mcp.server._client")
def test_zone_setup_prev_zone(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(zone_setup_prev_zone())
    fake.send_osc.assert_called_once_with("/beyond/zonesetup/prevzone", [])


@patch("beyond_mcp.server._client")
def test_zone_setup_select_param(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(zone_setup_select_param(5))
    fake.send_osc.assert_called_once_with("/beyond/zonesetup/param", [5.0])


@patch("beyond_mcp.server._client")
def test_zone_setup_next_param(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(zone_setup_next_param())
    fake.send_osc.assert_called_once_with("/beyond/zonesetup/nextparam", [])


@patch("beyond_mcp.server._client")
def test_zone_setup_prev_param(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(zone_setup_prev_param())
    fake.send_osc.assert_called_once_with("/beyond/zonesetup/prevparam", [])


@patch("beyond_mcp.server._client")
def test_zone_setup_set_xsize(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(zone_setup_set("xsize", 50.0))
    fake.send_osc.assert_called_once_with("/beyond/zonesetup/xsize", [50.0])


@patch("beyond_mcp.server._client")
def test_zone_setup_set_yposition(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(zone_setup_set("yposition", -25.0))
    fake.send_osc.assert_called_once_with("/beyond/zonesetup/yposition", [-25.0])


@patch("beyond_mcp.server._client")
def test_zone_setup_set_zrotation(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(zone_setup_set("zrotation", 45.0))
    fake.send_osc.assert_called_once_with("/beyond/zonesetup/zrotation", [45.0])


@patch("beyond_mcp.server._client")
def test_zone_setup_set_xkeystone(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(zone_setup_set("xkeystone", 10.0))
    fake.send_osc.assert_called_once_with("/beyond/zonesetup/xkeystone", [10.0])


@patch("beyond_mcp.server._client")
def test_zone_setup_set_corner_ax(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(zone_setup_set("ax", 100.0))
    fake.send_osc.assert_called_once_with("/beyond/zonesetup/ax", [100.0])


def test_zone_setup_set_invalid_parameter():
    payload = json.loads(zone_setup_set("invalid_param", 1.0))
    assert payload["ok"] is False
    assert "must be one of" in payload["error"]


# ================================================================
# Safety Limiter
# ================================================================


@patch("beyond_mcp.server._client")
def test_set_limiter_profile(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_limiter("profile", 2))
    fake.send_osc.assert_called_once_with("/beyond/general/SetLimiterProfile", [2])


@patch("beyond_mcp.server._client")
def test_set_limiter_per_zone(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_limiter("per_zone", 1))
    fake.send_osc.assert_called_once_with("/beyond/general/SetLimiterPerZone", [1])


@patch("beyond_mcp.server._client")
def test_set_limiter_per_grid(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_limiter("per_grid", 3))
    fake.send_osc.assert_called_once_with("/beyond/general/SetLimiterPerGrid", [3])


@patch("beyond_mcp.server._client")
def test_set_limiter_flash(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_limiter("flash", 0))
    fake.send_osc.assert_called_once_with("/beyond/general/SetLimiterFlash", [0])


@patch("beyond_mcp.server._client")
def test_set_limiter_hold(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_limiter("hold", 1))
    fake.send_osc.assert_called_once_with("/beyond/general/SetLimiterHold", [1])


@patch("beyond_mcp.server._client")
def test_set_limiter_beam(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_limiter("beam", 1))
    fake.send_osc.assert_called_once_with("/beyond/general/SetLimiterBeam", [1])


@patch("beyond_mcp.server._client")
def test_set_limiter_dmx(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_limiter("dmx", 5))
    fake.send_osc.assert_called_once_with("/beyond/general/SetLimiterDMX", [5])


@patch("beyond_mcp.server._client")
def test_set_limiter_show(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_limiter("show", 4))
    fake.send_osc.assert_called_once_with("/beyond/general/SetLimiterShow", [4])


def test_set_limiter_invalid_type():
    payload = json.loads(set_limiter("invalid_type", 1))
    assert payload["ok"] is False
    assert "must be one of" in payload["error"]


# ================================================================
# Display
# ================================================================


@patch("beyond_mcp.server._client")
def test_display_popup(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(display_popup("Hello BEYOND"))
    fake.send_osc.assert_called_once_with("/beyond/general/DisplayPopup", ["Hello BEYOND"])


@patch("beyond_mcp.server._client")
def test_display_preview_show(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(display_preview("main", 1))
    fake.send_osc.assert_called_once_with("/beyond/general/DisplayPreview", ["main", 1])


@patch("beyond_mcp.server._client")
def test_display_preview_hide(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(display_preview("main", 0))
    fake.send_osc.assert_called_once_with("/beyond/general/DisplayPreview", ["main", 0])


def test_display_preview_invalid_enabled():
    payload = json.loads(display_preview("main", 2))
    assert payload["ok"] is False


# ================================================================
# DMX / Channel Output
# ================================================================


@patch("beyond_mcp.server._client")
def test_channel_out(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(channel_out(1, 255))
    fake.send_osc.assert_called_once_with("/beyond/general/ChannelOut", [1, 255])


# ================================================================
# Control Scope
# ================================================================


@patch("beyond_mcp.server._client")
def test_set_control_scope_master(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_control_scope("master"))
    fake.send_osc.assert_called_once_with("/beyond/general/ControlMaster", [])


@patch("beyond_mcp.server._client")
def test_set_control_scope_cue(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_control_scope("cue", 2, 5))
    fake.send_osc.assert_called_once_with("/beyond/general/ControlCue", [2, 5])


@patch("beyond_mcp.server._client")
def test_set_control_scope_zone(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_control_scope("zone", 3))
    fake.send_osc.assert_called_once_with("/beyond/general/ControlZone", [3])


@patch("beyond_mcp.server._client")
def test_set_control_scope_track(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_control_scope("track", 1))
    fake.send_osc.assert_called_once_with("/beyond/general/ControlTrack", [1])


@patch("beyond_mcp.server._client")
def test_set_control_scope_projector(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_control_scope("projector", 0))
    fake.send_osc.assert_called_once_with("/beyond/general/ControlProjector", [0])


@patch("beyond_mcp.server._client")
def test_set_control_scope_smart(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(set_control_scope("smart", 7))
    fake.send_osc.assert_called_once_with("/beyond/general/ControlSmart", [7])


def test_set_control_scope_invalid():
    payload = json.loads(set_control_scope("invalid_scope"))
    assert payload["ok"] is False
    assert "must be one of" in payload["error"]


# ================================================================
# Virtual LJ
# ================================================================


@patch("beyond_mcp.server._client")
def test_virtual_lj_enable(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(virtual_lj(1))
    fake.send_osc.assert_called_once_with("/beyond/general/VirtualLJ", [1])


@patch("beyond_mcp.server._client")
def test_virtual_lj_disable(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(virtual_lj(0))
    fake.send_osc.assert_called_once_with("/beyond/general/VirtualLJ", [0])


def test_virtual_lj_invalid_enabled():
    payload = json.loads(virtual_lj(2))
    assert payload["ok"] is False


@patch("beyond_mcp.server._client")
def test_virtual_lj_fx(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    json.loads(virtual_lj_fx(0, 5))
    fake.send_osc.assert_called_once_with("/beyond/general/VLJFX", [0, 5])


# ================================================================
# Error handling
# ================================================================


@patch("beyond_mcp.server._client")
def test_osc_send_failure_returns_error(mock_client):
    fake = _fake_client()
    fake.send_osc.side_effect = OSError("Network unreachable")
    mock_client.return_value = fake
    payload = json.loads(blackout())
    assert payload["ok"] is False
    assert "OSC send failed" in payload["error"]


@patch("beyond_mcp.server._client")
def test_unexpected_exception_returns_error(mock_client):
    fake = _fake_client()
    fake.send_osc.side_effect = RuntimeError("Something broke")
    mock_client.return_value = fake
    payload = json.loads(enable_laser_output())
    assert payload["ok"] is False
    assert "Unexpected error" in payload["error"]
    assert "RuntimeError" in payload["error"]


# ================================================================
# Read-only mode
# ================================================================


def test_read_only_blocks_write_tools():
    os.environ["BEYOND_READ_ONLY"] = "1"
    try:
        payload = json.loads(blackout())
        assert payload["ok"] is False
        assert "read-only" in payload["error"]
    finally:
        os.environ.pop("BEYOND_READ_ONLY", None)


def test_read_only_blocks_send_osc_raw():
    os.environ["BEYOND_READ_ONLY"] = "1"
    try:
        payload = json.loads(send_osc_raw("/test", "[1]"))
        assert payload["ok"] is False
        assert "read-only" in payload["error"]
    finally:
        os.environ.pop("BEYOND_READ_ONLY", None)


def test_read_only_blocks_send_osc_bundle():
    os.environ["BEYOND_READ_ONLY"] = "1"
    try:
        payload = json.loads(send_osc_bundle('[["/test", []]]'))
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


def test_read_only_allows_health_check():
    os.environ["BEYOND_READ_ONLY"] = "1"
    try:
        # health_check does not call _check_write, so it should work
        # even though the client will fail to connect in test, the
        # function itself should not raise a read-only error
        payload = json.loads(health_check())
        # It may fail for OSError but not for read-only
        assert "read-only" not in payload.get("error", "")
    finally:
        os.environ.pop("BEYOND_READ_ONLY", None)


def test_read_only_allows_preview():
    os.environ["BEYOND_READ_ONLY"] = "1"
    try:
        payload = json.loads(preview_osc("/beyond/general/BlackOut", "[]"))
        assert payload["preview"] is True
    finally:
        os.environ.pop("BEYOND_READ_ONLY", None)


# ================================================================
# Confirm-destructive
# ================================================================


def _with_confirm_destructive(func, *args, **kwargs):
    """Helper to run a test with BEYOND_CONFIRM_DESTRUCTIVE=1."""
    os.environ["BEYOND_CONFIRM_DESTRUCTIVE"] = "1"
    try:
        return json.loads(func(*args, **kwargs))
    finally:
        os.environ.pop("BEYOND_CONFIRM_DESTRUCTIVE", None)


def test_blackout_requires_confirm():
    payload = _with_confirm_destructive(blackout)
    assert payload["ok"] is False
    assert "confirm=true" in payload["error"]


@patch("beyond_mcp.server._client")
def test_blackout_with_confirm(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    os.environ["BEYOND_CONFIRM_DESTRUCTIVE"] = "1"
    try:
        payload = json.loads(blackout(confirm=True))
        fake.send_osc.assert_called_once()
    finally:
        os.environ.pop("BEYOND_CONFIRM_DESTRUCTIVE", None)


def test_stop_all_now_requires_confirm():
    payload = _with_confirm_destructive(stop_all_now)
    assert payload["ok"] is False
    assert "confirm=true" in payload["error"]


@patch("beyond_mcp.server._client")
def test_stop_all_now_with_confirm(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    os.environ["BEYOND_CONFIRM_DESTRUCTIVE"] = "1"
    try:
        json.loads(stop_all_now(confirm=True))
        fake.send_osc.assert_called_once()
    finally:
        os.environ.pop("BEYOND_CONFIRM_DESTRUCTIVE", None)


def test_stop_all_sync_requires_confirm():
    payload = _with_confirm_destructive(stop_all_sync, 0.0)
    assert payload["ok"] is False
    assert "confirm=true" in payload["error"]


@patch("beyond_mcp.server._client")
def test_stop_all_sync_with_confirm(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    os.environ["BEYOND_CONFIRM_DESTRUCTIVE"] = "1"
    try:
        json.loads(stop_all_sync(0.0, confirm=True))
        fake.send_osc.assert_called_once()
    finally:
        os.environ.pop("BEYOND_CONFIRM_DESTRUCTIVE", None)


def test_stop_all_async_requires_confirm():
    payload = _with_confirm_destructive(stop_all_async, 0.0)
    assert payload["ok"] is False
    assert "confirm=true" in payload["error"]


@patch("beyond_mcp.server._client")
def test_stop_all_async_with_confirm(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    os.environ["BEYOND_CONFIRM_DESTRUCTIVE"] = "1"
    try:
        json.loads(stop_all_async(0.0, confirm=True))
        fake.send_osc.assert_called_once()
    finally:
        os.environ.pop("BEYOND_CONFIRM_DESTRUCTIVE", None)


def test_disable_laser_output_requires_confirm():
    payload = _with_confirm_destructive(disable_laser_output)
    assert payload["ok"] is False
    assert "confirm=true" in payload["error"]


@patch("beyond_mcp.server._client")
def test_disable_laser_output_with_confirm(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    os.environ["BEYOND_CONFIRM_DESTRUCTIVE"] = "1"
    try:
        json.loads(disable_laser_output(confirm=True))
        fake.send_osc.assert_called_once()
    finally:
        os.environ.pop("BEYOND_CONFIRM_DESTRUCTIVE", None)


def test_stop_zones_of_projector_requires_confirm():
    payload = _with_confirm_destructive(stop_zones_of_projector, 0)
    assert payload["ok"] is False
    assert "confirm=true" in payload["error"]


@patch("beyond_mcp.server._client")
def test_stop_zones_of_projector_with_confirm(mock_client):
    fake = _fake_client()
    mock_client.return_value = fake
    os.environ["BEYOND_CONFIRM_DESTRUCTIVE"] = "1"
    try:
        json.loads(stop_zones_of_projector(0, confirm=True))
        fake.send_osc.assert_called_once()
    finally:
        os.environ.pop("BEYOND_CONFIRM_DESTRUCTIVE", None)


# ================================================================
# Host allowlisting
# ================================================================


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


def test_custom_allowed_hosts():
    os.environ["BEYOND_HOST"] = "10.0.0.50"
    os.environ["BEYOND_ALLOWED_HOSTS"] = "10.0.0.50,192.168.1.1"
    try:
        payload = json.loads(get_server_config())
        assert payload["host"] == "10.0.0.50"
        assert "10.0.0.50" in payload["allowed_hosts"]
    finally:
        os.environ.pop("BEYOND_HOST", None)
        os.environ.pop("BEYOND_ALLOWED_HOSTS", None)


# ================================================================
# Transport validation
# ================================================================


def test_main_rejects_invalid_transport():
    from beyond_mcp.server import main

    os.environ["BEYOND_TRANSPORT"] = "websocket"
    try:
        with pytest.raises(ValueError, match="Invalid BEYOND_TRANSPORT"):
            main()
    finally:
        os.environ.pop("BEYOND_TRANSPORT", None)


# ================================================================
# Config edge cases
# ================================================================


def test_port_zero_rejected():
    from beyond_mcp.config import _parse_port

    os.environ["BEYOND_OSC_PORT"] = "0"
    try:
        with pytest.raises(ValueError, match="outside valid port range"):
            _parse_port("BEYOND_OSC_PORT", "12000")
    finally:
        os.environ.pop("BEYOND_OSC_PORT", None)


def test_port_65536_rejected():
    from beyond_mcp.config import _parse_port

    os.environ["BEYOND_OSC_PORT"] = "65536"
    try:
        with pytest.raises(ValueError, match="outside valid port range"):
            _parse_port("BEYOND_OSC_PORT", "12000")
    finally:
        os.environ.pop("BEYOND_OSC_PORT", None)


def test_port_non_integer_rejected():
    from beyond_mcp.config import _parse_port

    os.environ["BEYOND_OSC_PORT"] = "abc"
    try:
        with pytest.raises(ValueError, match="not a valid integer"):
            _parse_port("BEYOND_OSC_PORT", "12000")
    finally:
        os.environ.pop("BEYOND_OSC_PORT", None)


def test_port_valid_range():
    from beyond_mcp.config import _parse_port

    os.environ["BEYOND_OSC_PORT"] = "1"
    try:
        assert _parse_port("BEYOND_OSC_PORT", "12000") == 1
    finally:
        os.environ.pop("BEYOND_OSC_PORT", None)

    os.environ["BEYOND_OSC_PORT"] = "65535"
    try:
        assert _parse_port("BEYOND_OSC_PORT", "12000") == 65535
    finally:
        os.environ.pop("BEYOND_OSC_PORT", None)


def test_empty_allowed_hosts_rejected():
    from beyond_mcp.config import _parse_allowed_hosts

    with pytest.raises(ValueError, match="must contain at least one host"):
        _parse_allowed_hosts("")


def test_allowed_hosts_strips_whitespace():
    from beyond_mcp.config import _parse_allowed_hosts

    hosts = _parse_allowed_hosts("  host1 ,  host2  ")
    assert hosts == frozenset({"host1", "host2"})


# ================================================================
# Type tag mismatch (client)
# ================================================================


def test_type_tags_length_mismatch():
    from beyond_mcp.client import build_osc_message

    with pytest.raises(ValueError, match="type_tags length"):
        build_osc_message("/test", [1, 2], type_tags="i")


# ================================================================
# Tool count assertion
# ================================================================


def test_tool_count_is_117():
    from beyond_mcp.server import mcp as server_mcp

    tools = server_mcp._tool_manager._tools
    assert len(tools) == 117, (
        f"Expected 117 tools, got {len(tools)}: {sorted(tools.keys())}"
    )
