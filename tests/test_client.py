"""Tests for beyond_mcp.client — OSC message building, bundle building,
BeyondClient.send_osc, BeyondClient.send_bundle, and BeyondClient.health_check."""

import socket
import struct
from unittest.mock import MagicMock, patch

import pytest

from beyond_mcp.client import BeyondClient, build_osc_message, build_osc_bundle
from beyond_mcp.config import BeyondConfig


# ── build_osc_message ──────────────────────────────────────


def test_build_osc_message_rejects_non_absolute_address():
    with pytest.raises(ValueError, match="OSC address must start with '/'"):
        build_osc_message("beyond/master/brightness", [1.0])


def test_build_osc_message_encodes_int_float_and_string():
    packet = build_osc_message("/test", [7, 0.5, "go"])
    assert packet.startswith(b"/test\x00\x00\x00,ifs")
    assert struct.pack(">i", 7) in packet
    assert struct.pack(">f", 0.5) in packet
    assert b"go\x00\x00" in packet


def test_build_osc_message_supports_explicit_boolean_tags():
    packet = build_osc_message("/test", [True, False], type_tags="TF")
    assert packet == b"/test\x00\x00\x00,TF\x00"


def test_build_osc_message_infers_boolean_tags():
    packet = build_osc_message("/flag", [True, False])
    assert b",TF\x00" in packet


def test_build_osc_message_infers_none_tag():
    packet = build_osc_message("/nil", [None])
    assert b",N\x00\x00" in packet


def test_build_osc_message_type_tags_length_mismatch():
    with pytest.raises(ValueError, match="type_tags length"):
        build_osc_message("/test", [1, 2], type_tags="i")


def test_build_osc_message_unsupported_type_tag():
    with pytest.raises(ValueError, match="Unsupported OSC type tag"):
        build_osc_message("/test", [1], type_tags="X")


def test_build_osc_message_empty_values():
    packet = build_osc_message("/empty", [])
    assert b"/empty" in packet
    assert b",\x00\x00\x00" in packet


def test_build_osc_message_string_padding():
    """OSC strings must be null-terminated and padded to 4-byte boundary."""
    packet = build_osc_message("/s", ["ab"])
    # "ab" + null = 3 bytes, padded to 4 bytes
    assert b"ab\x00\x00" in packet


# ── build_osc_bundle ───────────────────────────────────────


def test_build_osc_bundle_starts_with_bundle_header():
    msg = build_osc_message("/test", [])
    bundle = build_osc_bundle([msg])
    assert bundle.startswith(b"#bundle\x00")


def test_build_osc_bundle_immediate_timetag():
    msg = build_osc_message("/test", [1])
    bundle = build_osc_bundle([msg])
    # Immediately after "#bundle\0" (8 bytes), the timetag is 8 bytes
    timetag = bundle[8:16]
    assert timetag == b"\x00\x00\x00\x00\x00\x00\x00\x01"


def test_build_osc_bundle_custom_timetag():
    msg = build_osc_message("/test", [])
    bundle = build_osc_bundle([msg], timetag=42)
    timetag = bundle[8:16]
    assert timetag == struct.pack(">Q", 42)


def test_build_osc_bundle_contains_message_length_prefix():
    msg = build_osc_message("/test", [])
    bundle = build_osc_bundle([msg])
    # After header (8) + timetag (8) = 16, next 4 bytes are message length
    msg_len = struct.unpack(">i", bundle[16:20])[0]
    assert msg_len == len(msg)


def test_build_osc_bundle_multiple_messages():
    m1 = build_osc_message("/a", [1])
    m2 = build_osc_message("/b", [2])
    bundle = build_osc_bundle([m1, m2])
    # Both messages should be in the bundle
    assert b"/a\x00\x00" in bundle
    assert b"/b\x00\x00" in bundle


def test_build_osc_bundle_empty_list():
    bundle = build_osc_bundle([])
    assert bundle == b"#bundle\x00" + b"\x00\x00\x00\x00\x00\x00\x00\x01"


# ── BeyondClient.send_osc ─────────────────────────────────


@patch("beyond_mcp.client.socket.socket")
@patch("beyond_mcp.client.socket.getaddrinfo")
def test_send_osc_returns_metadata(mock_getaddrinfo, mock_sock_cls):
    mock_getaddrinfo.return_value = [
        (socket.AF_INET, socket.SOCK_DGRAM, 17, "", ("127.0.0.1", 12000)),
    ]
    mock_sock = MagicMock()
    mock_sock_cls.return_value = mock_sock

    config = BeyondConfig(host="127.0.0.1", osc_port=12000)
    client = BeyondClient(config=config)
    result = client.send_osc("/test/addr", [42])

    assert result["address"] == "/test/addr"
    assert result["values"] == [42]
    assert result["host"] == "127.0.0.1"
    assert result["port"] == 12000
    assert result["bytes_sent"] > 0
    assert result["type_tags"] == "i"
    mock_sock.sendto.assert_called_once_with(mock_sock.sendto.call_args[0][0], ("127.0.0.1", 12000))
    mock_sock.close.assert_called_once()


@patch("beyond_mcp.client.socket.socket")
@patch("beyond_mcp.client.socket.getaddrinfo")
def test_send_osc_explicit_type_tags(mock_getaddrinfo, mock_sock_cls):
    mock_getaddrinfo.return_value = [
        (socket.AF_INET, socket.SOCK_DGRAM, 17, "", ("127.0.0.1", 12000)),
    ]
    mock_sock = MagicMock()
    mock_sock_cls.return_value = mock_sock

    config = BeyondConfig(host="127.0.0.1", osc_port=12000)
    client = BeyondClient(config=config)
    result = client.send_osc("/test", [1.0], type_tags="f")

    assert result["type_tags"] == "f"


# ── BeyondClient.send_bundle ──────────────────────────────


@patch("beyond_mcp.client.socket.socket")
@patch("beyond_mcp.client.socket.getaddrinfo")
def test_send_bundle_returns_metadata(mock_getaddrinfo, mock_sock_cls):
    mock_getaddrinfo.return_value = [
        (socket.AF_INET, socket.SOCK_DGRAM, 17, "", ("127.0.0.1", 12000)),
    ]
    mock_sock = MagicMock()
    mock_sock_cls.return_value = mock_sock

    config = BeyondConfig(host="127.0.0.1", osc_port=12000)
    client = BeyondClient(config=config)
    result = client.send_bundle([("/a", [1]), ("/b", [2])])

    assert result["bundle"] is True
    assert result["message_count"] == 2
    assert result["host"] == "127.0.0.1"
    assert result["port"] == 12000
    assert result["bytes_sent"] > 0
    assert len(result["messages"]) == 2
    assert result["messages"][0] == {"address": "/a", "values": [1]}
    assert result["messages"][1] == {"address": "/b", "values": [2]}
    mock_sock.sendto.assert_called_once_with(mock_sock.sendto.call_args[0][0], ("127.0.0.1", 12000))
    mock_sock.close.assert_called_once()


@patch("beyond_mcp.client.socket.socket")
@patch("beyond_mcp.client.socket.getaddrinfo")
def test_send_bundle_custom_timetag(mock_getaddrinfo, mock_sock_cls):
    mock_getaddrinfo.return_value = [
        (socket.AF_INET, socket.SOCK_DGRAM, 17, "", ("127.0.0.1", 12000)),
    ]
    mock_sock = MagicMock()
    mock_sock_cls.return_value = mock_sock

    config = BeyondConfig(host="127.0.0.1", osc_port=12000)
    client = BeyondClient(config=config)
    result = client.send_bundle([("/a", [])], timetag=99)

    assert result["bundle"] is True
    # Verify the bundle bytes sent contain the custom timetag
    sent_data = mock_sock.sendto.call_args[0][0]
    assert struct.pack(">Q", 99) in sent_data


@patch("beyond_mcp.client.socket.socket")
@patch("beyond_mcp.client.socket.getaddrinfo")
def test_send_bundle_empty_messages(mock_getaddrinfo, mock_sock_cls):
    mock_getaddrinfo.return_value = [
        (socket.AF_INET, socket.SOCK_DGRAM, 17, "", ("127.0.0.1", 12000)),
    ]
    mock_sock = MagicMock()
    mock_sock_cls.return_value = mock_sock

    config = BeyondConfig(host="127.0.0.1", osc_port=12000)
    client = BeyondClient(config=config)
    result = client.send_bundle([])

    assert result["message_count"] == 0
    assert result["messages"] == []


# ── BeyondClient.health_check ─────────────────────────────


@patch("beyond_mcp.client.socket.socket")
@patch("beyond_mcp.client.socket.getaddrinfo")
def test_health_check_reachable(mock_getaddrinfo, mock_sock_cls):
    mock_getaddrinfo.return_value = [
        (2, 2, 17, "", ("127.0.0.1", 12000)),
    ]
    mock_sock = MagicMock()
    mock_sock_cls.return_value = mock_sock

    config = BeyondConfig(host="127.0.0.1", osc_port=12000)
    client = BeyondClient(config=config)
    result = client.health_check()

    assert result["reachable"] is True
    assert result["host"] == "127.0.0.1"
    assert result["port"] == 12000
    assert "elapsed_ms" in result
    mock_sock.connect.assert_called_once_with(("127.0.0.1", 12000))
    mock_sock.close.assert_called_once()


@patch("beyond_mcp.client.socket.socket")
@patch("beyond_mcp.client.socket.getaddrinfo")
def test_send_osc_supports_ipv6_targets(mock_getaddrinfo, mock_sock_cls):
    mock_getaddrinfo.return_value = [
        (socket.AF_INET6, socket.SOCK_DGRAM, 17, "", ("::1", 12000, 0, 0)),
    ]
    mock_sock = MagicMock()
    mock_sock_cls.return_value = mock_sock

    config = BeyondConfig(host="::1", osc_port=12000, allowed_hosts=frozenset({"::1"}))
    client = BeyondClient(config=config)
    result = client.send_osc("/test/addr", [42])

    assert result["host"] == "::1"
    mock_sock_cls.assert_called_once_with(socket.AF_INET6, socket.SOCK_DGRAM, 17)
    mock_sock.sendto.assert_called_once_with(mock_sock.sendto.call_args[0][0], ("::1", 12000, 0, 0))


@patch("beyond_mcp.client.socket.getaddrinfo")
def test_health_check_unresolvable(mock_getaddrinfo):
    mock_getaddrinfo.return_value = []

    config = BeyondConfig(host="badhost.invalid", osc_port=12000)
    client = BeyondClient(config=config)
    result = client.health_check()

    assert result["reachable"] is False
    assert "Cannot resolve" in result["error"]


@patch("beyond_mcp.client.socket.getaddrinfo")
def test_health_check_os_error(mock_getaddrinfo):
    mock_getaddrinfo.side_effect = OSError("Network is down")

    config = BeyondConfig(host="127.0.0.1", osc_port=12000)
    client = BeyondClient(config=config)
    result = client.health_check()

    assert result["reachable"] is False
    assert "Network is down" in result["error"]
    assert "elapsed_ms" in result
