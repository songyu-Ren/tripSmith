from __future__ import annotations

import datetime as dt
from typing import Any

from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict


class TripCreateRequest(BaseModel):
    origin: str
    destination: str
    start_date: dt.date
    end_date: dt.date
    flexible_days: int = 0
    budget_total: float
    currency: str = "USD"
    travelers: int = 1
    preferences: dict[str, Any] = Field(default_factory=dict)


class TripDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    created_at: dt.datetime
    origin: str
    destination: str
    start_date: dt.date
    end_date: dt.date
    flexible_days: int
    budget_total: float
    currency: str
    travelers: int
    preferences: dict[str, Any]

