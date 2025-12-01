from __future__ import annotations

"""Entrypoint for the GPT-Quick-TTS console app."""

import os
import sys
from typing import Optional

from .async_utils import AsyncLoopThread
from .audio import AudioOutput
from .config import ConfigStore
from .engine import TTSEngine
from .openai_client import OpenAITTSClient
from .state import ConsoleState
from .styles import DEFAULT_STYLES, VOICES, StyleState
from .ui.app import ConsoleApp


def _resolve_api_key(config_store: ConfigStore) -> Optional[str]:
    cfg = config_store.load()
    key = cfg.api_key or os.getenv("OPENAI_API_KEY")
    if key:
        return key

    # Prompt user once before launching UI (best-effort).
    try:
        print("\nOpenAI API key not set.")
        api_input = input("Enter your OpenAI API key (leave empty to continue without): ").strip()
    except Exception:
        return None

    if api_input:
        cfg.api_key = api_input
        config_store.save(cfg)
        try:
            os.environ["OPENAI_API_KEY"] = api_input
        except Exception:
            pass
        return api_input
    return None


def build_app() -> ConsoleApp:
    config_store = ConfigStore()
    styles = StyleState(DEFAULT_STYLES)
    voices = VOICES

    api_key = _resolve_api_key(config_store)
    async_runner = AsyncLoopThread()
    client = OpenAITTSClient(api_key=api_key, async_runner=async_runner)
    audio = AudioOutput()
    engine = TTSEngine(client, audio)
    state = ConsoleState(config_store, styles, voices)

    if not audio.available():
        err = audio.describe_error() or "unknown reason"
        state.add_log(f"Audio initialization failed: {err}")

    def shutdown():
        async_runner.stop(timeout=2.0)

    return ConsoleApp(state, engine, on_shutdown=shutdown)


def main():
    try:
        app = build_app()
        app.run()
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
