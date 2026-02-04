from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ApiException(Exception):
    status_code: int
    error_code: str
    message: str
    details: object | None = None
    headers: dict[str, str] | None = None
