from __future__ import annotations

import re
from typing import Any


_SAFE_TEXT_RE = re.compile(r"[^\w\s,.;:/+\-()#]", re.UNICODE)
_EMAIL_RE = re.compile(r"(?i)\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b")
_PHONE_RE = re.compile(r"(?:(?<=\D)|^)(?:\+?\d[\d\s().-]{7,}\d)(?:(?=\D)|$)")


def sanitize_text(value: str) -> str:
    value = value.strip()
    value = _SAFE_TEXT_RE.sub("", value)
    return value[:256]


def redact_text(value: str) -> str:
    value = _EMAIL_RE.sub("[REDACTED_EMAIL]", value)
    value = _PHONE_RE.sub("[REDACTED_PHONE]", value)
    return value


def redact_obj(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, str):
        return redact_text(obj)
    if isinstance(obj, (int, float, bool)):
        return obj
    if isinstance(obj, list):
        return [redact_obj(v) for v in obj]
    if isinstance(obj, tuple):
        return [redact_obj(v) for v in obj]
    if isinstance(obj, dict):
        redacted: dict[Any, Any] = {}
        for k, v in obj.items():
            key = redact_text(k) if isinstance(k, str) else k
            redacted[key] = redact_obj(v)
        return redacted
    return str(obj)

