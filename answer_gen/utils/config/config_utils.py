from __future__ import annotations

from configparser import ConfigParser

config_manager: ConfigParser | None = None

def read_config(config_path: str) -> ConfigParser:
    """Read an INI config file and return a ConfigParser.

    Raises FileNotFoundError if the config file cannot be read.
    """
    global config_manager
    if config_manager is not None:
        return config_manager

    if not config_path:
        raise FileNotFoundError("Config path was not provided")

    config = ConfigParser()
    if not config.read(config_path):
        raise FileNotFoundError(f"Config not found at {config_path}")

    config_manager = config
    return config_manager


def _ensure_loaded() -> ConfigParser:
    """Return the loaded config or raise if `read_config` was not called."""
    if config_manager is None:
        raise RuntimeError("Config not loaded; call read_config first")
    return config_manager


def get_config_str(section: str, key: str, fallback: str) -> str:
    """Fetch and normalize a string config value (trim + remove surrounding quotes)."""
    cfg = _ensure_loaded()
    return cfg.get(section, key, fallback=fallback).strip().strip('"').strip("'")


def get_config_int(section: str, key: str, fallback: int) -> int:
    """Fetch a config value and cast it to an integer."""
    cfg = _ensure_loaded()
    return int(cfg.get(section, key, fallback=fallback))


def get_config_float(section: str, key: str, fallback: float) -> float:
    """Fetch a config value and cast it to a float."""
    cfg = _ensure_loaded()
    return float(cfg.get(section, key, fallback=fallback))
