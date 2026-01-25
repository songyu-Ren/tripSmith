from __future__ import annotations

import datetime as dt

from tripsmith.schemas.itinerary import ItineraryJson
from tripsmith.schemas.plan import PlansJson


def verify_plans(*, trip_budget: float, plans: PlansJson) -> list[str]:
    issues: list[str] = []
    for opt in plans.options:
        if opt.metrics.total_price.amount > trip_budget:
            issues.append(f"{opt.label}: over budget")
    return issues


def verify_itinerary(*, itinerary: ItineraryJson) -> list[str]:
    issues: list[str] = []
    for day in itinerary.days:
        total_stay = sum(i.stay_minutes for i in day.items)
        total_commute = sum(i.commute.minutes for i in day.items)
        if total_stay > 8 * 60:
            issues.append(f"{day.date.isoformat()}: too many activities")
        if total_commute > 2 * 60:
            issues.append(f"{day.date.isoformat()}: commute too long")
    return issues


def trip_days(start: dt.date, end: dt.date) -> list[dt.date]:
    days = (end - start).days + 1
    return [start + dt.timedelta(days=i) for i in range(days)]

