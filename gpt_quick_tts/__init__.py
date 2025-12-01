"""GPT-Quick-TTS package exports.

This package isolates the main building blocks (config, styles, OpenAI client,
audio output, state management, and the prompt-toolkit UI) so the application
can be reused or extended without relying on a single monolithic script.
"""
from .config import AppConfig, ConfigStore, default_config_path
from .styles import DEFAULT_STYLES, VOICES, StyleState, build_style_prefix
from .audio import AudioOutput
from .openai_client import OpenAITTSClient
from .engine import TTSEngine, TTSCallbacks
from .state import ConsoleState
from .ui.app import ConsoleApp

__all__ = [
    "AppConfig",
    "ConfigStore",
    "default_config_path",
    "DEFAULT_STYLES",
    "VOICES",
    "StyleState",
    "build_style_prefix",
    "AudioOutput",
    "OpenAITTSClient",
    "TTSEngine",
    "TTSCallbacks",
    "ConsoleState",
    "ConsoleApp",
]
