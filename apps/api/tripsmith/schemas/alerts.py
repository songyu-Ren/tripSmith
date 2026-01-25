from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict


class AlertCreateRequest(BaseModel):
    trip_id: str
    type: Literal["flight", "hotel", "both"]
    threshold: float
    frequency_minutes: int


class AlertDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    trip_id: str
    type: str
    threshold: float
    frequency_minutes: int
    last_checked_at: dt.datetime | None
    is_active: bool


class AlertCreateResponse(BaseModel):
    alert: AlertDto

