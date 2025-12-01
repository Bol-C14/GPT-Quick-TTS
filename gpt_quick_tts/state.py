from __future__ import annotations

"""Mutable state for the console app (voice, styles, logs, status)."""

import threading
from collections import deque
from datetime import datetime
from typing import Deque, List

from .config import AppConfig, ConfigStore
from .styles import StyleState


class ConsoleState:
    def __init__(self, config_store: ConfigStore, styles: StyleState, voices: List[str]):
        self._lock = threading.Lock()
        self._logs: Deque[str] = deque(maxlen=20)
        self._config_store = config_store
        self.styles = styles
        self.voices = voices
        self.status = "Initializing"
        self.voice = voices[0] if voices else "alloy"
        self.streaming = False

        cfg = self._config_store.load()
        cfg.ensure_style_defaults(self.styles.names)
        self._apply_config(cfg)
        self.status = "Idle"

    def _apply_config(self, cfg: AppConfig) -> None:
        if cfg.voice in self.voices:
            self.voice = cfg.voice
        self.streaming = bool(cfg.streaming)
        self.styles.update_from_config(cfg.styles)
        self._persist(cfg)

    def _persist(self, cfg: AppConfig) -> None:
        cfg.voice = self.voice
        cfg.streaming = self.streaming
        cfg.styles = self.styles.to_config()
        self._config_store.save(cfg)

    def _load_config(self) -> AppConfig:
        cfg = self._config_store.load()
        cfg.ensure_style_defaults(self.styles.names)
        return cfg

    # Logging helpers
    def add_log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        with self._lock:
            self._logs.append(f"[{timestamp}] {message}")

    def logs(self) -> List[str]:
        with self._lock:
            return list(self._logs)

    # Status helpers
    def set_status(self, status: str) -> None:
        self.status = status

    # Style / voice toggles
    def toggle_style(self, name: str) -> bool:
        new_state = self.styles.toggle(name)
        cfg = self._load_config()
        self._persist(cfg)
        return new_state

    def toggle_streaming(self) -> bool:
        self.streaming = not self.streaming
        cfg = self._load_config()
        self._persist(cfg)
        return self.streaming

    def cycle_voice(self) -> str:
        if not self.voices:
            return self.voice
        try:
            idx = self.voices.index(self.voice)
        except ValueError:
            idx = 0
        idx = (idx + 1) % len(self.voices)
        self.voice = self.voices[idx]
        cfg = self._load_config()
        self._persist(cfg)
        return self.voice
