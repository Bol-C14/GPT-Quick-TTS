"""Compatibility wrapper around the new OpenAI client."""
from __future__ import annotations

from gpt_quick_tts.openai_client import OPENAI_API_KEY, OPENAI_BASE_URL, OpenAITTSClient as TTSClient

__all__ = ["TTSClient", "OPENAI_BASE_URL", "OPENAI_API_KEY"]
