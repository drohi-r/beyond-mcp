import pytest

from beyond_mcp.config import load_config


@pytest.fixture(autouse=True)
def clear_beyond_env(monkeypatch):
    for key in (
        "BEYOND_HOST",
        "BEYOND_OSC_PORT",
        "BEYOND_ALLOWED_HOSTS",
        "BEYOND_SAFETY_PROFILE",
        "BEYOND_READ_ONLY",
        "BEYOND_CONFIRM_DESTRUCTIVE",
    ):
        monkeypatch.delenv(key, raising=False)


def test_load_config_default_lab_profile():
    config = load_config()
    assert config.safety_profile == "lab"
    assert config.read_only is False
    assert config.confirm_destructive is False


def test_load_config_show_safe_profile(monkeypatch):
    monkeypatch.setenv("BEYOND_SAFETY_PROFILE", "show-safe")
    config = load_config()
    assert config.safety_profile == "show-safe"
    assert config.read_only is False
    assert config.confirm_destructive is True


def test_load_config_read_only_profile(monkeypatch):
    monkeypatch.setenv("BEYOND_SAFETY_PROFILE", "read-only")
    config = load_config()
    assert config.safety_profile == "read-only"
    assert config.read_only is True
    assert config.confirm_destructive is True


def test_load_config_profile_can_be_overridden(monkeypatch):
    monkeypatch.setenv("BEYOND_SAFETY_PROFILE", "show-safe")
    monkeypatch.setenv("BEYOND_CONFIRM_DESTRUCTIVE", "0")
    config = load_config()
    assert config.safety_profile == "show-safe"
    assert config.confirm_destructive is False


def test_load_config_invalid_profile(monkeypatch):
    monkeypatch.setenv("BEYOND_SAFETY_PROFILE", "unsafe")
    with pytest.raises(ValueError, match="BEYOND_SAFETY_PROFILE"):
        load_config()
