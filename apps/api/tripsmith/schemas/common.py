from __future__ import annotations

from pydantic import BaseModel


class ApiError(BaseModel):
    code: str
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    error: ApiError

