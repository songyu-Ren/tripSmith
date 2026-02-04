from __future__ import annotations

from tripsmith.schemas.constraints import Constraints


def generate_constraints(*, trip: dict) -> Constraints:
    prefs = trip.get("preferences") or {}
    tags = prefs.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    tags_set = {str(t).lower() for t in tags if t}

    pace = "balanced"
    if "relaxed" in tags_set:
        pace = "relaxed"
    if "packed" in tags_set:
        pace = "packed"

    walking = 6.0
    if pace == "relaxed":
        walking = 3.0
    if pace == "packed":
        walking = 10.0

    return Constraints(
        pace=pace,
        walking_tolerance_km_per_day=walking,
        max_daily_activity_hours=8,
        max_daily_commute_hours=2,
        max_transfer_count=2,
        hotel_star_min=None,
        night_flight_allowed=False,
    )

