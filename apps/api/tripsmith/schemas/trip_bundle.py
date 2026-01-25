from __future__ import annotations

from pydantic import BaseModel

from tripsmith.schemas.plan import PlansJson
from tripsmith.schemas.trips import TripDto


class TripGetResponse(BaseModel):
    trip: TripDto
    latest_plan_id: str | None
    latest_plans_json: PlansJson | None
    latest_explain_md: str | None

