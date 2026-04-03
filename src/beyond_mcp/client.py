from __future__ import annotations

import socket
import struct
from dataclasses import dataclass
from typing import Any

from .config import BeyondConfig


def _pad_osc_string(value: str) -> bytes:
    data = value.encode("utf-8") + b"\x00"
    while len(data) % 4 != 0:
        data += b"\x00"
    return data


def _infer_osc_type_tag(value: Any) -> str:
    if isinstance(value, bool):
        return "T" if value else "F"
    if isinstance(value, int) and not isinstance(value, bool):
        return "i"
    if isinstance(value, float):
        return "f"
    if value is None:
        return "N"
    return "s"


def build_osc_message(address: str, values: list[Any], *, type_tags: str | None = None) -> bytes:
    if not address.startswith("/"):
        raise ValueError("OSC address must start with '/'.")

    tags = type_tags or "".join(_infer_osc_type_tag(value) for value in values)
    if len(tags) != len(values):
        raise ValueError("type_tags length must match values length.")

    encoded_values = bytearray()
    for tag, value in zip(tags, values, strict=True):
        if tag == "i":
            encoded_values.extend(struct.pack(">i", int(value)))
        elif tag == "f":
            encoded_values.extend(struct.pack(">f", float(value)))
        elif tag == "s":
            encoded_values.extend(_pad_osc_string(str(value)))
        elif tag in {"T", "F", "N"}:
            continue
        else:
            raise ValueError(f"Unsupported OSC type tag: {tag!r}")

    return _pad_osc_string(address) + _pad_osc_string(f",{tags}") + bytes(encoded_values)


@dataclass
class BeyondClient:
    config: BeyondConfig

    def send_osc(
        self,
        address: str,
        values: list[Any],
        *,
        host: str | None = None,
        port: int | None = None,
        type_tags: str | None = None,
    ) -> dict[str, Any]:
        target_host = host or self.config.host
        target_port = port or self.config.osc_port
        packet = build_osc_message(address, values, type_tags=type_tags)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.sendto(packet, (target_host, target_port))
        finally:
            sock.close()
        return {
            "address": address,
            "values": values,
            "type_tags": type_tags or "".join(_infer_osc_type_tag(value) for value in values),
            "host": target_host,
            "port": target_port,
            "bytes_sent": len(packet),
        }
