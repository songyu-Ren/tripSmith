from __future__ import annotations

from typing import Literal

from pydantic import BaseModel
from pydantic import Field


class Constraints(BaseModel):
    pace: Literal["relaxed", "balanced", "packed"] = "balanced"
    walking_tolerance_km_per_day: float = Field(ge=0, le=50)
    max_daily_activity_hours: float = Field(default=8, ge=0, le=24)
    max_daily_commute_hours: float = Field(default=2, ge=0, le=24)
    max_transfer_count: int = Field(ge=0, le=10)
    hotel_star_min: int | None = Field(default=None, ge=1, le=5)
    night_flight_allowed: bool = False


class ConstraintsGenerateResponse(BaseModel):
    constraints: Constraints


class ConstraintsUpdateRequest(BaseModel):
    constraints: Constraints


class ConstraintsGetResponse(BaseModel):
    constraints: Constraints | None
    confirmed: bool

