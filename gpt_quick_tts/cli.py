from __future__ import annotations

"""Entrypoint for the GPT-Quick-TTS console app."""

import argparse
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


def _parse_args(argv: list[str]):
    parser = argparse.ArgumentParser(description="GPT-Quick-TTS console", add_help=True)
    parser.add_argument(
        "--install-virtual-mic",
        action="store_true",
        help="Install a virtual microphone (VB-Cable) on Windows, then exit.",
    )
    parser.add_argument(
        "--force-virtual-mic",
        action="store_true",
        help="Force virtual mic install even if the device appears present.",
    )
    return parser.parse_args(argv)


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


def _maybe_install_virtual_mic(from_flag: bool, force: bool) -> bool:
    """Return True if install path handled (flag requested), False otherwise."""
    should_auto = os.getenv("TTS_AUTO_INSTALL_VIRTUAL_MIC", "").lower() in {"1", "true", "yes"}
    force_auto = os.getenv("TTS_FORCE_VIRTUAL_MIC", "").lower() in {"1", "true", "yes"}

    if not from_flag and not should_auto:
        return False

    try:
        from .virtual_mic import install_virtual_cable
    except Exception as exc:
        print(f"Virtual mic helper unavailable: {exc}")
        return from_flag

    requested_force = force or force_auto
    ok = install_virtual_cable(force=requested_force)
    if from_flag:
        sys.exit(0 if ok else 1)
    return False


def main(argv: Optional[list[str]] = None):
    args = _parse_args(list(argv) if argv is not None else sys.argv[1:])
    _maybe_install_virtual_mic(from_flag=args.install_virtual_mic, force=args.force_virtual_mic)

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
