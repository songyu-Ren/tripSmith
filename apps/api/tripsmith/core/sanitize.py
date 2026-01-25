from __future__ import annotations

import re


_SAFE_TEXT_RE = re.compile(r"[^\w\s,.;:/+\-()#]", re.UNICODE)


def sanitize_text(value: str) -> str:
    value = value.strip()
    value = _SAFE_TEXT_RE.sub("", value)
    return value[:256]

