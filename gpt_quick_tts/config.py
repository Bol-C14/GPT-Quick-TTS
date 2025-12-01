from __future__ import annotations

"""Configuration helpers for GPT-Quick-TTS."""

import json
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


DEFAULT_CONFIG_FILENAME = "tts_config.json"


def default_config_path() -> Path:
    """Resolve the config path, allowing an override via TTS_CONFIG_PATH."""
    env_path = os.getenv("TTS_CONFIG_PATH")
    if env_path:
        return Path(env_path).expanduser()
    return Path(__file__).resolve().parent.parent / DEFAULT_CONFIG_FILENAME


@dataclass
class AppConfig:
    """Serialized configuration for the console app."""

    voice: str = "alloy"
    streaming: bool = False
    api_key: Optional[str] = None
    styles: Dict[str, bool] = field(default_factory=dict)

    def ensure_style_defaults(self, style_names: list[str]) -> None:
        """Add missing style keys so toggling is predictable."""
        for name in style_names:
            self.styles.setdefault(name, False)

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "AppConfig":
        return cls(
            voice=str(data.get("voice", "alloy")),
            streaming=bool(data.get("streaming", False)),
            api_key=data.get("api_key") or None,
            styles=dict(data.get("styles") or {}),
        )

    def to_dict(self) -> Dict[str, object]:
        return {
            "voice": self.voice,
            "streaming": bool(self.streaming),
            "api_key": self.api_key,
            "styles": dict(self.styles),
        }


class ConfigStore:
    """Thread-safe loader/saver for AppConfig."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or default_config_path()
        self._lock = threading.Lock()

    def load(self) -> AppConfig:
        if not self.path.exists():
            return AppConfig()

        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return AppConfig.from_dict(data)
        except Exception:
            # Fall back to defaults if file is corrupted.
            return AppConfig()

    def save(self, cfg: AppConfig) -> None:
        with self._lock:
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("w", encoding="utf-8") as f:
                    json.dump(cfg.to_dict(), f, indent=2, ensure_ascii=False)
            except Exception:
                # Best-effort; do not raise to the UI.
                return
