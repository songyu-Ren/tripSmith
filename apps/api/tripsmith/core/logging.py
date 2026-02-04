from __future__ import annotations

import json
import logging
import os
import sys
import time
from typing import Any

from tripsmith.core.sanitize import redact_obj


_LOGGER = logging.getLogger("tripsmith")
_NO_REDACT_KEYS = {"request_id", "path", "method", "latency_ms", "status_code", "user_id", "trip_id"}


def configure_logging() -> None:
    if _LOGGER.handlers:
        return
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    _LOGGER.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    _LOGGER.addHandler(handler)
    _LOGGER.propagate = False


def log_event(event: str, **fields: Any) -> None:
    configure_logging()
    cleaned: dict[str, Any] = {}
    for k, v in fields.items():
        cleaned[k] = v if k in _NO_REDACT_KEYS else redact_obj(v)
    payload = {"event": event, "ts": time.time(), **cleaned}
    try:
        _LOGGER.info(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    except Exception:
        _LOGGER.info('{"event":"log_failed"}')
