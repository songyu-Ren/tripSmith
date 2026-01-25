from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel
from pydantic import Field


class Commute(BaseModel):
    mode: Literal["walk", "drive", "transit", "estimate"]
    minutes: int


class ItineraryItem(BaseModel):
    period: Literal["morning", "afternoon", "evening"]
    poi_name: str
    stay_minutes: int
    commute: Commute
    weather_summary: str


class ItineraryDay(BaseModel):
    date: dt.date
    items: list[ItineraryItem]


class ItineraryJson(BaseModel):
    generated_at: dt.datetime
    plan_index: int
    days: list[ItineraryDay]


class ItineraryCreateRequest(BaseModel):
    plan_index: int = Field(ge=0, le=2)


class ItineraryCreateResponse(BaseModel):
    itinerary_id: str
    itinerary_json: ItineraryJson
    itinerary_md: str

