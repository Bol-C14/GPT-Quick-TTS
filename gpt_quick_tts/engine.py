from __future__ import annotations

"""Service layer responsible for turning text into audio and playing it."""

from dataclasses import dataclass
from typing import Callable, Optional

from .audio import AudioOutput
from .openai_client import OpenAITTSClient
from .styles import StyleState


@dataclass
class TTSCallbacks:
    on_status: Optional[Callable[[str], None]] = None
    on_log: Optional[Callable[[str], None]] = None

    def log(self, message: str) -> None:
        if self.on_log:
            self.on_log(message)

    def status(self, status: str) -> None:
        if self.on_status:
            self.on_status(status)


class TTSEngine:
    """High-level engine that orchestrates TTS requests and playback."""

    def __init__(self, client: OpenAITTSClient, audio: AudioOutput, model: str = "gpt-4o-mini-tts"):
        self.client = client
        self.audio = audio
        self.model = model

    def speak(self, text: str, voice: str, styles: StyleState, streaming: bool, callbacks: Optional[TTSCallbacks] = None) -> None:
        callbacks = callbacks or TTSCallbacks()
        raw_text = text.strip()
        if not raw_text:
            return

        if not self.audio.available():
            callbacks.status("Error")
            callbacks.log("Error: Audio playback not available")
            callbacks.status("Idle")
            return

        prefix = styles.build_prefix()
        full_text = prefix + raw_text

        callbacks.log(f"Processing: {raw_text[:50]}...")
        callbacks.status("Sending")

        if streaming:
            try:
                self.client.stream_and_play(self.model, voice, full_text)
                callbacks.log("Streaming playback completed")
                callbacks.status("Idle")
                return
            except Exception as exc:
                callbacks.log(f"Streaming failed, falling back: {exc}")

        if not self.audio.available():
            callbacks.status("Error")
            callbacks.log("Error: Audio playback not available")
            callbacks.status("Idle")
            return

        try:
            audio_bytes = self.client.synthesize(self.model, voice, full_text)
        except Exception as exc:
            callbacks.status("Error")
            callbacks.log(f"Error generating audio: {exc}")
            callbacks.status("Idle")
            return

        callbacks.status("Playing")
        callbacks.log("Playing audio...")

        try:
            self.audio.play_bytes(audio_bytes)
        except Exception as exc:
            callbacks.status("Error")
            callbacks.log(f"Error during playback: {exc}")
            callbacks.status("Idle")
            return

        callbacks.status("Idle")
        callbacks.log("Playback completed")
