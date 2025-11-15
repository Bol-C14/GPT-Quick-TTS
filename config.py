"""Simple JSON config helper for GPT-Quick-TTS.

Stores small user preferences like last voice, streaming mode, and style toggles
in a `tts_config.json` file at the project root (same folder as this file).
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict


CONFIG_FILENAME = "tts_config.json"


def _default_config() -> Dict[str, Any]:
    return {
        "voice": "alloy",
        "streaming": False,
        # API key (optional) - can be set interactively and persisted
        "api_key": None,
        # styles is a mapping style_name -> bool
        "styles": {},
    }


def config_path() -> Path:
    # store in project root (same dir as this module)
    return Path(__file__).parent / CONFIG_FILENAME


def load_config() -> Dict[str, Any]:
    path = config_path()
    if not path.exists():
        return _default_config()
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure defaults for missing keys
            cfg = _default_config()
            cfg.update({k: v for k, v in data.items() if v is not None})
            return cfg
    except Exception:
        # On parse error, return defaults (do not raise)
        return _default_config()


def save_config(cfg: Dict[str, Any]) -> None:
    path = config_path()
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        # best-effort; don't raise on IO errors
        pass
