"""Wrapper around OpenAI TTS interactions.

Provides a simple TTSClient that returns audio bytes for given text,
model and voice. Keeps the OpenAI-specific code out of the UI module.
"""
import os
from typing import Optional
from openai import OpenAI
from async_runner import AsyncLoopThread


class TTSClient:
    def __init__(self, api_key: Optional[str] = None):
        # Use provided api_key or rely on environment variable
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = OpenAI()
        # Async runner for streaming tasks (created on demand)
        self._async_runner: Optional[AsyncLoopThread] = None

    def synthesize(self, model: str, voice: str, input_text: str, instructions: Optional[str] = None) -> bytes:
        """Synthesize `input_text` using specified model and voice.

        Returns raw audio bytes (mp3 by default unless response_format set differently).
        """
        kwargs = dict(model=model, voice=voice, input=input_text)
        if instructions:
            kwargs['instructions'] = instructions

        # Synchronous request returning full content (keeps API usage simple)
        response = self.client.audio.speech.create(**kwargs)
        # response.content contains bytes
        return response.content

    def stream_synthesize_and_play(self, model: str, voice: str, input_text: str, instructions: Optional[str] = None) -> None:
        """Attempt to stream audio from the TTS API and play it in near-realtime.

        This uses AsyncOpenAI and openai.helpers.LocalAudioPlayer when available.
        It will raise RuntimeError if streaming support isn't available in the
        installed OpenAI helper package.
        """
        try:
            from openai import AsyncOpenAI
            from openai.helpers import LocalAudioPlayer
        except Exception as e:
            raise RuntimeError("Streaming playback not available: missing AsyncOpenAI/LocalAudioPlayer") from e

        async def _stream_and_play():
            openai_async = AsyncOpenAI()
            params = dict(model=model, voice=voice, input=input_text)
            if instructions:
                params['instructions'] = instructions
            # Use pcm for lowest latency when possible
            params['response_format'] = 'pcm'

            async with openai_async.audio.speech.with_streaming_response.create(**params) as response:
                await LocalAudioPlayer().play(response)

        # Use a dedicated async runner thread to execute the coroutine safely
        try:
            if not self._async_runner:
                self._async_runner = AsyncLoopThread()
            # run_coroutine will block until completion or timeout
            self._async_runner.run_coroutine(_stream_and_play())
        except Exception:
            # Propagate to caller so they can fallback to non-streaming
            raise
