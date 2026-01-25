from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel
from pydantic import Field


class Money(BaseModel):
    amount: float
    currency: str


class FlightSummary(BaseModel):
    depart_at: str
    arrive_at: str
    stops: int
    duration_minutes: int
    price: Money


class StaySummary(BaseModel):
    name: str
    area: str
    nightly_price: Money
    total_price: Money


class PlanScores(BaseModel):
    cost_score: float = Field(ge=0, le=100)
    time_score: float = Field(ge=0, le=100)
    comfort_score: float = Field(ge=0, le=100)


class PlanMetrics(BaseModel):
    total_price: Money
    total_flight_minutes: int
    transfer_count: int
    daily_commute_minutes_estimate: int


class PlanOption(BaseModel):
    label: Literal["cheap", "fast", "balanced"]
    title: str
    flight: FlightSummary
    stay: StaySummary
    metrics: PlanMetrics
    scores: PlanScores
    explanation: str
    warnings: list[str] = Field(default_factory=list)


class PlansJson(BaseModel):
    generated_at: dt.datetime
    options: list[PlanOption]


class PlanCreateResponse(BaseModel):
    plan_id: str
    plans_json: PlansJson
    explain_md: str

