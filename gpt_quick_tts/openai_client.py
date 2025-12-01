from __future__ import annotations

"""Wrapper around OpenAI's TTS endpoints."""

import os
from typing import Optional

from openai import OpenAI

from .async_utils import AsyncLoopThread

# Optional base URL to route OpenAI-compatible requests through a proxy.
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class OpenAITTSClient:
    """Small wrapper that keeps OpenAI specifics out of UI code."""

    def __init__(self, api_key: Optional[str] = None, async_runner: Optional[AsyncLoopThread] = None):
        client_kwargs = {}
        key = api_key or OPENAI_API_KEY
        if key:
            client_kwargs["api_key"] = key
        if OPENAI_BASE_URL:
            client_kwargs["base_url"] = OPENAI_BASE_URL

        self.client = OpenAI(**client_kwargs)
        self._async_runner = async_runner

    def synthesize(self, model: str, voice: str, text: str, instructions: Optional[str] = None) -> bytes:
        """Return raw audio bytes for the provided text."""
        kwargs = {"model": model, "voice": voice, "input": text}
        if instructions:
            kwargs["instructions"] = instructions
        response = self.client.audio.speech.create(**kwargs)
        return response.content

    def stream_and_play(self, model: str, voice: str, text: str, instructions: Optional[str] = None) -> None:
        """Stream audio and play it locally with low latency."""
        try:
            from openai import AsyncOpenAI
            from openai.helpers import LocalAudioPlayer
        except Exception as exc:
            raise RuntimeError("Streaming playback not available: missing AsyncOpenAI/LocalAudioPlayer") from exc

        async def _stream():
            async_kwargs = {}
            key = getattr(self.client, "api_key", None) or OPENAI_API_KEY
            if key:
                async_kwargs["api_key"] = key
            if OPENAI_BASE_URL:
                async_kwargs["base_url"] = OPENAI_BASE_URL

            async_client = AsyncOpenAI(**async_kwargs)
            params = {"model": model, "voice": voice, "input": text, "response_format": "pcm"}
            if instructions:
                params["instructions"] = instructions

            async with async_client.audio.speech.with_streaming_response.create(**params) as response:
                await LocalAudioPlayer().play(response)

        runner = self._async_runner or AsyncLoopThread()
        runner.run_coroutine(_stream())
