from __future__ import annotations

"""Wrapper around OpenAI's TTS endpoints."""

import os
from typing import Optional

from openai import OpenAI

from .async_utils import AsyncLoopThread

# Optional base URL to route OpenAI-compatible requests through a proxy.
# Default to the proxy path for api.castralhub.com/openai/v1 so packaged EXEs
# will use the forwarding URL unless overridden by the environment.
DEFAULT_BASE_URL = "https://api.castralhub.com/openai/v1"
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", DEFAULT_BASE_URL)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class OpenAITTSClient:
    """Small wrapper that keeps OpenAI specifics out of UI code."""

    def __init__(self, api_key: Optional[str] = None, async_runner: Optional[AsyncLoopThread] = None):
        self._async_runner = async_runner
        self._api_key = api_key or OPENAI_API_KEY
        self._base_url = OPENAI_BASE_URL
        self.client: Optional[OpenAI] = None

        if self._api_key:
            self.client = self._build_client(self._api_key)

    def _build_client(self, api_key: str) -> OpenAI:
        kwargs = {"api_key": api_key}
        if self._base_url:
            kwargs["base_url"] = self._base_url
        return OpenAI(**kwargs)

    def _ensure_client(self) -> OpenAI:
        if self.client:
            return self.client

        key = self._api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Set the environment variable or save it in the app before generating audio."
            )

        self._api_key = key
        self.client = self._build_client(key)
        return self.client

    def synthesize(self, model: str, voice: str, text: str, instructions: Optional[str] = None) -> bytes:
        """Return raw audio bytes for the provided text."""
        client = self._ensure_client()
        kwargs = {"model": model, "voice": voice, "input": text}
        if instructions:
            kwargs["instructions"] = instructions
        response = client.audio.speech.create(**kwargs)
        return response.content

    def stream_and_play(self, model: str, voice: str, text: str, instructions: Optional[str] = None) -> None:
        """Stream audio and play it locally with low latency."""
        try:
            from openai import AsyncOpenAI
            from openai.helpers import LocalAudioPlayer
        except Exception as exc:
            raise RuntimeError("Streaming playback not available: missing AsyncOpenAI/LocalAudioPlayer") from exc

        async def _stream():
            client = self._ensure_client()
            async_kwargs = {"api_key": getattr(client, "api_key", None)}
            if self._base_url:
                async_kwargs["base_url"] = self._base_url

            async_client = AsyncOpenAI(**async_kwargs)
            params = {"model": model, "voice": voice, "input": text, "response_format": "pcm"}
            if instructions:
                params["instructions"] = instructions

            async with async_client.audio.speech.with_streaming_response.create(**params) as response:
                await LocalAudioPlayer().play(response)

        runner = self._async_runner or AsyncLoopThread()
        runner.run_coroutine(_stream())
