from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


JobType = Literal["plan", "itinerary"]
JobStatus = Literal["queued", "running", "succeeded", "failed"]


class JobDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    trip_id: str
    type: JobType
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    message: str
    result_json: dict | None
    created_at: dt.datetime
    updated_at: dt.datetime


class JobCreateResponse(BaseModel):
    job_id: str

