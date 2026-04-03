from __future__ import annotations

import os
from dataclasses import dataclass, field

_DEFAULT_ALLOWED_HOSTS = "127.0.0.1,localhost,::1"


def _parse_port(env_name: str, default: str) -> int:
    raw = os.getenv(env_name, default)
    try:
        port = int(raw)
    except ValueError:
        raise ValueError(f"{env_name}={raw!r} is not a valid integer") from None
    if not (1 <= port <= 65535):
        raise ValueError(f"{env_name}={port} is outside valid port range 1-65535")
    return port


def _parse_allowed_hosts(raw: str) -> frozenset[str]:
    hosts = frozenset(h.strip() for h in raw.split(",") if h.strip())
    if not hosts:
        raise ValueError("BEYOND_ALLOWED_HOSTS must contain at least one host")
    return hosts


@dataclass(frozen=True)
class BeyondConfig:
    host: str = "127.0.0.1"
    osc_port: int = 12000
    allowed_hosts: frozenset[str] = field(default_factory=lambda: frozenset({"127.0.0.1", "localhost", "::1"}))
    read_only: bool = False
    confirm_destructive: bool = False

    @property
    def target(self) -> str:
        return f"{self.host}:{self.osc_port}"

    def check_host_allowed(self) -> None:
        if "*" in self.allowed_hosts:
            return
        if self.host not in self.allowed_hosts:
            raise ValueError(
                f"Host {self.host!r} is not in BEYOND_ALLOWED_HOSTS. "
                f"Allowed: {', '.join(sorted(self.allowed_hosts))}. "
                f"Set BEYOND_ALLOWED_HOSTS=* to allow any host."
            )


def load_config() -> BeyondConfig:
    host = os.getenv("BEYOND_HOST", "127.0.0.1")
    allowed_raw = os.getenv("BEYOND_ALLOWED_HOSTS", _DEFAULT_ALLOWED_HOSTS)
    read_only = os.getenv("BEYOND_READ_ONLY", "0").lower() in ("1", "true", "yes")
    confirm_destructive = os.getenv("BEYOND_CONFIRM_DESTRUCTIVE", "0").lower() in ("1", "true", "yes")

    config = BeyondConfig(
        host=host,
        osc_port=_parse_port("BEYOND_OSC_PORT", "12000"),
        allowed_hosts=_parse_allowed_hosts(allowed_raw),
        read_only=read_only,
        confirm_destructive=confirm_destructive,
    )
    config.check_host_allowed()
    return config
