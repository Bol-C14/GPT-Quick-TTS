"""Compatibility config helpers delegating to the new package."""
from __future__ import annotations

from typing import Any, Dict

from gpt_quick_tts.config import AppConfig, ConfigStore, default_config_path

_store = ConfigStore(default_config_path())


def load_config() -> Dict[str, Any]:
    """Return a plain dict version of the config."""
    return _store.load().to_dict()


def save_config(cfg: Dict[str, Any]) -> None:
    """Persist a config dict."""
    _store.save(AppConfig.from_dict(cfg))


__all__ = ["load_config", "save_config", "default_config_path", "AppConfig", "ConfigStore"]
