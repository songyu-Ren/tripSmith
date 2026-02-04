from __future__ import annotations

import datetime as dt

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class SavedPlanDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    trip_id: str
    plan_id: str
    plan_index: int
    created_at: dt.datetime
    label: str


class SavePlanRequest(BaseModel):
    plan_id: str
    plan_index: int = Field(ge=0)
    label: str = Field(min_length=1, max_length=64)


class SavePlanResponse(BaseModel):
    saved_plan: SavedPlanDto


class SavedPlansListResponse(BaseModel):
    saved_plans: list[SavedPlanDto]

