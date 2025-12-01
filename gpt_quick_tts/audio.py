"""Audio playback helper using pygame."""
from __future__ import annotations

import tempfile
from pathlib import Path
import pygame


class AudioPlayer:
    """Thin wrapper around pygame.mixer for blocking playback."""

    def __init__(self):
        self._audio_available = False
        try:
            pygame.mixer.init()
        except Exception:
            self._audio_available = False
        else:
            self._audio_available = True

    def available(self) -> bool:
        return self._audio_available

    def play_bytes(self, audio_bytes: bytes) -> None:
        """Play provided audio bytes (assumed to be an MP3 by default)."""
        if not self._audio_available:
            raise RuntimeError("Audio playback not available")

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".mp3", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_filename = tmp.name

        try:
            pygame.mixer.music.load(tmp_filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(20)
        finally:
            try:
                Path(tmp_filename).unlink()
            except Exception:
                pass

    def quit(self):
        if self._audio_available:
            pygame.mixer.quit()


# Backwards-compatible name expected across the codebase
# some modules import `AudioOutput` — provide it as an alias to AudioPlayer
AudioOutput = AudioPlayer
