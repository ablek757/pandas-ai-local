"""Extract the first ```python ...``` fenced block from an LLM response."""

from __future__ import annotations

import re

_FENCE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_code(text: str) -> str:
    m = _FENCE.search(text)
    if m:
        return m.group(1).strip()
    # Fallback: the model might have returned raw code.
    return text.strip()
