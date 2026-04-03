import struct

import pytest

from beyond_mcp.client import build_osc_message


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
