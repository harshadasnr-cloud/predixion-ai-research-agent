"""Cheap prompt-injection screening for retrieved text (defence in depth)."""
import re

_PATTERNS = [
    r"ignore (all |any |the )?(previous|prior|above|earlier) (instructions|prompts?)",
    r"disregard (all |any |the )?.{0,40}instructions",
    r"you are now\b",
    r"(reveal|print|show|output) .{0,30}(system prompt|api key|secret)",
    r"new instructions\s*:",
    r"(always |must )?cite (this|the following) (url|site|source)",
]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in _PATTERNS]
PLACEHOLDER = "[removed: possible prompt injection]"


def neutralize(text: str) -> tuple[str, bool]:
    """Return (cleaned_text, was_flagged)."""
    flagged = False
    for pattern in _COMPILED:
        text, n = pattern.subn(PLACEHOLDER, text)
        flagged = flagged or n > 0
    return text, flagged
