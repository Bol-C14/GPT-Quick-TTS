"""Compatibility surface for legacy imports."""
from __future__ import annotations

from gpt_quick_tts.styles import (
    DEFAULT_STYLES,
    VOICES,
    StyleDefinition,
    StyleState,
    build_style_prefix,
)

# Expose a mapping matching the previous STYLE_TOKENS constant.
STYLE_TOKENS = {definition.name: definition.token for definition in DEFAULT_STYLES}

__all__ = [
    "STYLE_TOKENS",
    "DEFAULT_STYLES",
    "VOICES",
    "StyleDefinition",
    "StyleState",
    "build_style_prefix",
]
