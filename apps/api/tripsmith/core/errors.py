from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ErrorCategory(str, Enum):
    VALIDATION = "VALIDATION"
    PROVIDER = "PROVIDER"
    LLM = "LLM"
    JOB = "JOB"
    RATE_LIMIT = "RATE_LIMIT"
    INTERNAL = "INTERNAL"


def make_error_code(category: ErrorCategory, code: str) -> str:
    return f"{category.value}.{code}"


@dataclass
class ApiException(Exception):
    status_code: int
    error_code: str
    message: str
    details: object | None = None
    headers: dict[str, str] | None = None
