from __future__ import annotations

import socket
import struct
import time
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


def build_osc_bundle(messages: list[bytes], *, timetag: int | None = None) -> bytes:
    """Build an OSC bundle from a list of pre-built OSC messages.

    The timetag is an NTP-format 64-bit timestamp. If None, uses the
    'immediately' timetag (0x0000000000000001).
    """
    bundle = bytearray(b"#bundle\x00")
    if timetag is None:
        bundle.extend(b"\x00\x00\x00\x00\x00\x00\x00\x01")
    else:
        bundle.extend(struct.pack(">Q", timetag))
    for msg in messages:
        bundle.extend(struct.pack(">i", len(msg)))
        bundle.extend(msg)
    return bytes(bundle)


@dataclass
class BeyondClient:
    config: BeyondConfig

    def _resolve_udp_target(self) -> tuple[int, int, int, tuple[Any, ...]]:
        addr_info = socket.getaddrinfo(
            self.config.host,
            self.config.osc_port,
            type=socket.SOCK_DGRAM,
        )
        if not addr_info:
            raise OSError(f"Cannot resolve {self.config.host}")
        family, socktype, proto, _canonname, sockaddr = addr_info[0]
        return family, socktype, proto, sockaddr

    def send_osc(
        self,
        address: str,
        values: list[Any],
        *,
        type_tags: str | None = None,
    ) -> dict[str, Any]:
        target_host = self.config.host
        target_port = self.config.osc_port
        packet = build_osc_message(address, values, type_tags=type_tags)
        family, socktype, proto, sockaddr = self._resolve_udp_target()
        sock = socket.socket(family, socktype, proto)
        try:
            sock.sendto(packet, sockaddr)
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

    def send_bundle(
        self,
        messages: list[tuple[str, list[Any]]],
        *,
        timetag: int | None = None,
    ) -> dict[str, Any]:
        """Send multiple OSC messages as an atomic bundle."""
        target_host = self.config.host
        target_port = self.config.osc_port
        packets = [build_osc_message(addr, vals) for addr, vals in messages]
        bundle = build_osc_bundle(packets, timetag=timetag)
        family, socktype, proto, sockaddr = self._resolve_udp_target()
        sock = socket.socket(family, socktype, proto)
        try:
            sock.sendto(bundle, sockaddr)
        finally:
            sock.close()
        return {
            "bundle": True,
            "message_count": len(messages),
            "messages": [{"address": addr, "values": vals} for addr, vals in messages],
            "host": target_host,
            "port": target_port,
            "bytes_sent": len(bundle),
        }

    def health_check(self) -> dict[str, Any]:
        """Verify that the target host is resolvable and a UDP socket can be created."""
        target_host = self.config.host
        target_port = self.config.osc_port
        start = time.monotonic()
        try:
            family, socktype, proto, sockaddr = self._resolve_udp_target()
            sock = socket.socket(family, socktype, proto)
            try:
                sock.connect(sockaddr)
            finally:
                sock.close()
            elapsed_ms = round((time.monotonic() - start) * 1000, 1)
            return {
                "reachable": True,
                "host": target_host,
                "port": target_port,
                "elapsed_ms": elapsed_ms,
            }
        except OSError as exc:
            elapsed_ms = round((time.monotonic() - start) * 1000, 1)
            return {
                "reachable": False,
                "host": target_host,
                "port": target_port,
                "error": str(exc),
                "elapsed_ms": elapsed_ms,
            }
