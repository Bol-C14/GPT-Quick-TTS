from __future__ import annotations

"""Style tokens, voices, and helpers."""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence


@dataclass(frozen=True)
class StyleDefinition:
    name: str
    token: str
    hotkey: Optional[str] = None
    default: bool = False


DEFAULT_STYLES: List[StyleDefinition] = [
    StyleDefinition("Teaching", "<<style:teaching, clear, friendly>>", hotkey="t"),
    StyleDefinition("Calm", "<<style:calm, gentle>>", hotkey="c"),
    StyleDefinition("Excited", "<<style:excited, energetic>>", hotkey="e"),
    StyleDefinition("Narration", "<<style:narration, warm, paced>>", hotkey="n"),
    StyleDefinition("Questioning", "<<style:questioning, curious, rising>>", hotkey="q"),
    StyleDefinition("Warm", "<<style:warm, soft>>", hotkey="w"),
    StyleDefinition("Formal", "<<style:formal, precise>>", hotkey="f"),
    StyleDefinition("Angry", "<<style:angry, terse, forceful>>", hotkey="a"),
    StyleDefinition("Sarcastic", "<<style:sarcastic, wry, ironic>>", hotkey="s"),
    StyleDefinition("Serious", "<<style:serious, measured>>", hotkey="r"),
    StyleDefinition("Playful", "<<style:playful, light, whimsical>>", hotkey="p"),
    StyleDefinition("Whisper", "<<style:whisper, soft, intimate>>", hotkey="h"),
    StyleDefinition("Confident", "<<style:confident, assertive>>", hotkey="o"),
    StyleDefinition("Melancholic", "<<style:melancholic, slow, soft>>", hotkey="m"),
    StyleDefinition("Dramatic", "<<style:dramatic, emphatic>>", hotkey="d"),
    StyleDefinition("Cheerful", "<<style:cheerful, bright>>", hotkey="l"),
]

VOICES: List[str] = [
    "alloy",
    "ash",
    "ballad",
    "coral",
    "echo",
    "fable",
    "nova",
    "onyx",
    "sage",
    "shimmer",
]


class StyleState:
    """Track which styles are active and provide view-friendly accessors."""

    def __init__(self, definitions: Sequence[StyleDefinition], initial: Optional[Dict[str, bool]] = None):
        self._definitions = {d.name: d for d in definitions}
        self._order = list(definitions)
        initial = initial or {}
        self._state: Dict[str, bool] = {}
        for definition in self._order:
            self._state[definition.name] = bool(initial.get(definition.name, definition.default))

    @property
    def names(self) -> List[str]:
        return list(self._definitions.keys())

    @property
    def order(self) -> List[StyleDefinition]:
        return list(self._order)

    def is_active(self, name: str) -> bool:
        return bool(self._state.get(name, False))

    def toggle(self, name: str) -> bool:
        if name not in self._state:
            # Unknown styles are initialized on first toggle.
            self._state[name] = True
            return True
        self._state[name] = not self._state[name]
        return self._state[name]

    def set(self, name: str, value: bool) -> None:
        if name not in self._state:
            self._state[name] = bool(value)
        else:
            self._state[name] = bool(value)

    def update_from_config(self, cfg_styles: Dict[str, bool]) -> None:
        for name, active in (cfg_styles or {}).items():
            if name in self._state:
                self._state[name] = bool(active)

    def to_config(self) -> Dict[str, bool]:
        return dict(self._state)

    def build_prefix(self) -> str:
        """Return concatenated control tokens for active styles."""
        tokens = []
        for definition in self._order:
            if self._state.get(definition.name):
                tokens.append(definition.token)
        return "".join(tokens)

    def display_items(self) -> List[tuple[StyleDefinition, bool]]:
        """Return (definition, active) for rendering."""
        return [(definition, self._state.get(definition.name, False)) for definition in self._order]

    def hotkey_lookup(self) -> Dict[str, str]:
        """Return lowercase hotkey -> style name mapping."""
        mapping: Dict[str, str] = {}
        for definition in self._order:
            if definition.hotkey:
                mapping[definition.hotkey.lower()] = definition.name
        return mapping


def build_style_prefix(styles: Dict[str, bool], definitions: Iterable[StyleDefinition] = DEFAULT_STYLES) -> str:
    """Helper for compatibility: build prefix from a dict of style -> active."""
    ordered_defs = list(definitions)
    tokens = []
    for definition in ordered_defs:
        if styles.get(definition.name):
            tokens.append(definition.token)
    return "".join(tokens)
