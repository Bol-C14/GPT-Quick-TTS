"""Style and voice configuration for GPT-Quick-TTS.

This module centralizes STYLE_TOKENS, available VOICES and helpers for
building control-token prefixes for the TTS model.
"""
from typing import Dict, List

# Control-like tokens sent to the TTS model (less likely to be read verbatim)
STYLE_TOKENS: Dict[str, str] = {
    'Teaching': "<<style:teaching, clear, friendly>>",
    'Calm': "<<style:calm, gentle>>",
    'Excited': "<<style:excited, energetic>>",
    # Extra styles for extended control
    'Narration': "<<style:narration, warm, paced>>",
    'Questioning': "<<style:questioning, curious, rising>>",
    'Warm': "<<style:warm, soft>>",
    'Formal': "<<style:formal, precise>>",
    # Additional expressive styles
    'Angry': "<<style:angry, terse, forceful>>",
    'Sarcastic': "<<style:sarcastic, wry, ironic>>",
    'Serious': "<<style:serious, measured>>",
    'Playful': "<<style:playful, light, whimsical>>",
    'Whisper': "<<style:whisper, soft, intimate>>",
    'Confident': "<<style:confident, assertive>>",
    'Melancholic': "<<style:melancholic, slow, soft>>",
    'Dramatic': "<<style:dramatic, emphatic>>",
    'Cheerful': "<<style:cheerful, bright>>",
}

# A simple ordered list of voices supported by the TTS model (from docs)
VOICES: List[str] = [
    'alloy', 'ash', 'ballad', 'coral', 'echo', 'fable',
    'nova', 'onyx', 'sage', 'shimmer', 'alloy',
]

def build_style_prefix(styles: Dict[str, bool]) -> str:
    """Return concatenated control tokens for active styles.

    styles: mapping of style-name -> bool (active)
    """
    tokens = []
    for name, active in styles.items():
        if active:
            tok = STYLE_TOKENS.get(name)
            if tok:
                tokens.append(tok)
    return "".join(tokens)
