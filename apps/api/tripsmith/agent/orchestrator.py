from __future__ import annotations

import datetime as dt
import hashlib
import json
import time

from redis import Redis

from tripsmith.agent.optimizer import choose_plans
from tripsmith.agent.optimizer import compute_scorecard
from tripsmith.agent.verifier import trip_days
from tripsmith.agent.verifier import verify_itinerary
from tripsmith.agent.verifier import verify_plans
from tripsmith.core.sanitize import redact_obj
from tripsmith.providers.base import GeoPoint
from tripsmith.providers.base import PoiCandidate
from tripsmith.providers.registry import get_flights_provider
from tripsmith.providers.registry import get_poi_provider
from tripsmith.providers.registry import get_routing_provider
from tripsmith.providers.registry import get_stays_provider
from tripsmith.providers.registry import get_weather_provider
from tripsmith.schemas.itinerary import Commute
from tripsmith.schemas.itinerary import ItineraryDay
from tripsmith.schemas.itinerary import ItineraryItem
from tripsmith.schemas.itinerary import ItineraryJson
from tripsmith.schemas.plan import FlightSummary
from tripsmith.schemas.plan import Money
from tripsmith.schemas.plan import PlanMetrics
from tripsmith.schemas.plan import PlanOption
from tripsmith.schemas.plan import PlansJson
from tripsmith.schemas.plan import PlanScorecard
from tripsmith.schemas.plan import PlanScores
from tripsmith.schemas.plan import StaySummary


def _cache_key(prefix: str, payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"cache:{prefix}:{h}"


async def _cached(redis: Redis, *, key: str, ttl_seconds: int, fn):
    hit = redis.get(key)
    if hit is not None:
        return json.loads(hit)
    value = await fn()
    redis.setex(key, ttl_seconds, json.dumps(value))
    return value


def _to_geo(stay_location: GeoPoint) -> GeoPoint:
    return GeoPoint(lat=float(stay_location.lat), lon=float(stay_location.lon))


def _center_from_stay(stay_location: GeoPoint) -> GeoPoint:
    return GeoPoint(lat=float(stay_location.lat), lon=float(stay_location.lon))


async def generate_plans(*, redis: Redis, trip: dict) -> tuple[PlansJson, str, list[dict]]:
    flights_provider = get_flights_provider()
    stays_provider = get_stays_provider()
    routing_provider = get_routing_provider()
    tool_calls: list[dict] = []

    def record(tool: str, input_json: dict, output_json: object, *, started: float):
        tool_calls.append(
            {
                "tool": tool,
                "input": redact_obj(input_json),
                "output": redact_obj(output_json),
                "latency_ms": int((time.perf_counter() - started) * 1000),
            }
        )

    start_date = trip["start_date"].isoformat() if isinstance(trip["start_date"], dt.date) else str(trip["start_date"])
    end_date = trip["end_date"].isoformat() if isinstance(trip["end_date"], dt.date) else str(trip["end_date"])

    flights_payload = {
        "origin": trip["origin"],
        "destination": trip["destination"],
        "start_date": start_date,
        "end_date": end_date,
        "travelers": int(trip["travelers"]),
    }
    stays_payload = {
        "destination": trip["destination"],
        "start_date": start_date,
        "end_date": end_date,
        "travelers": int(trip["travelers"]),
        "budget_total": float(trip["budget_total"]),
    }

    async def fetch_flights():
        started = time.perf_counter()
        results = await flights_provider.search(**flights_payload)
        out = [r.__dict__ for r in results]
        record(type(flights_provider).__name__ + ".search", flights_payload, {"count": len(out), "items": out[:3]}, started=started)
        return out

    async def fetch_stays():
        started = time.perf_counter()
        results = await stays_provider.search(**stays_payload)
        out = [
            {
                **r.__dict__,
                "location": {"lat": r.location.lat, "lon": r.location.lon},
            }
            for r in results
        ]
        record(type(stays_provider).__name__ + ".search", stays_payload, {"count": len(out), "items": out[:3]}, started=started)
        return out

    flights_raw = await _cached(redis, key=_cache_key("flights", flights_payload), ttl_seconds=60 * 30, fn=fetch_flights)
    stays_raw = await _cached(redis, key=_cache_key("stays", stays_payload), ttl_seconds=60 * 30, fn=fetch_stays)

    from tripsmith.providers.base import FlightCandidate
    from tripsmith.providers.base import StayCandidate

    flights = [FlightCandidate(**f) for f in flights_raw][:20]
    stays = [StayCandidate(**{**s, "location": GeoPoint(**s["location"])}) for s in stays_raw][:20]

    started = time.perf_counter()
    commute_est = await routing_provider.estimate(from_point=_to_geo(stays[0].location), to_point=_to_geo(stays[1].location), mode="transit")
    record(
        type(routing_provider).__name__ + ".estimate",
        {"from": {"lat": stays[0].location.lat, "lon": stays[0].location.lon}, "to": {"lat": stays[1].location.lat, "lon": stays[1].location.lon}, "mode": "transit"},
        commute_est.__dict__,
        started=started,
    )
    daily_commute_est = int(commute_est.minutes)

    chosen = choose_plans(flights=flights, stays=stays, budget_total=float(trip["budget_total"]), daily_commute_minutes_estimate=daily_commute_est)
    options: list[PlanOption] = []
    for label in ("cheap", "fast", "balanced"):
        c = chosen[label]
        total_cost = float(c.flight.price_amount) + float(c.stay.total_price_amount)
        scorecard = compute_scorecard(
            total_cost=total_cost,
            currency=str(c.stay.currency),
            budget_total=float(trip["budget_total"]),
            flight_minutes=int(c.flight.duration_minutes),
            stops=int(c.flight.stops),
            commute_minutes=int(c.daily_commute_minutes_estimate),
        )
        cost_score = float(scorecard["cost_score"])
        time_score = float(scorecard["time_score"])
        comfort_score = float(scorecard["comfort_score"])
        commute_score = float(scorecard["commute_score"])
        daily_load_score = float(scorecard["daily_load_score"])
        warnings: list[str] = []
        if total_cost > float(trip["budget_total"]):
            warnings.append("Budget may be insufficient; this option exceeds your budget")
        if c.flight.stops >= 2:
            warnings.append("Many transfers; watch visas and baggage connections")
        rationale_md = (
            f"- Cost score: {cost_score:.0f}/100 (budget {float(trip['budget_total']):.0f})\n"
            f"- Time score: {time_score:.0f}/100 (flight {int(c.flight.duration_minutes)} min)\n"
            f"- Comfort score: {comfort_score:.0f}/100 (transfers {int(c.flight.stops)})\n"
            f"- Commute score: {commute_score:.0f}/100 (daily commute est. {int(c.daily_commute_minutes_estimate)} min)\n"
            f"- Daily load score: {daily_load_score:.0f}/100\n"
        )
        options.append(
            PlanOption(
                label=label,
                title={"cheap": "Budget option", "fast": "Time-saver option", "balanced": "Balanced option"}[label],
                flight=FlightSummary(
                    depart_at=c.flight.depart_at,
                    arrive_at=c.flight.arrive_at,
                    stops=int(c.flight.stops),
                    duration_minutes=int(c.flight.duration_minutes),
                    price=Money(amount=float(c.flight.price_amount), currency=str(c.flight.currency)),
                ),
                stay=StaySummary(
                    name=c.stay.name,
                    area=c.stay.area,
                    nightly_price=Money(amount=float(c.stay.nightly_price_amount), currency=str(c.stay.currency)),
                    total_price=Money(amount=float(c.stay.total_price_amount), currency=str(c.stay.currency)),
                ),
                metrics=PlanMetrics(
                    total_price=Money(amount=float(total_cost), currency=str(c.stay.currency)),
                    total_flight_minutes=int(c.flight.duration_minutes),
                    transfer_count=int(c.flight.stops),
                    daily_commute_minutes_estimate=int(c.daily_commute_minutes_estimate),
                ),
                scorecard=PlanScorecard(
                    total_cost=float(scorecard["total_cost"]),
                    currency=str(scorecard["currency"]),
                    total_travel_time_hours=float(scorecard["total_travel_time_hours"]),
                    num_transfers=int(scorecard["num_transfers"]),
                    daily_load_score=daily_load_score,
                    commute_score=commute_score,
                    comfort_score=comfort_score,
                    cost_score=cost_score,
                    time_score=time_score,
                    rationale_md=rationale_md,
                ),
                scores=PlanScores(
                    daily_load_score=daily_load_score,
                    commute_score=commute_score,
                    comfort_score=comfort_score,
                    cost_score=cost_score,
                    time_score=time_score,
                ),
                explanation=_explain(label, cost_score, time_score, comfort_score, warnings),
                warnings=warnings,
            )
        )

    plans = PlansJson(generated_at=dt.datetime.now(dt.timezone.utc), options=options)
    issues = verify_plans(trip_budget=float(trip["budget_total"]), plans=plans)
    if issues:
        for opt in plans.options:
            if opt.metrics.total_price.amount > float(trip["budget_total"]):
                opt.warnings.append("System check: budget constraint cannot be satisfied; returning the closest option")

    explain_md = render_plans_markdown(trip=trip, plans=plans)
    return plans, explain_md, tool_calls


async def generate_itinerary(*, redis: Redis, trip: dict, plan: PlansJson, plan_index: int) -> tuple[ItineraryJson, str, list[dict]]:
    poi_provider = get_poi_provider()
    weather_provider = get_weather_provider()
    routing_provider = get_routing_provider()
    tool_calls: list[dict] = []

    def record(tool: str, input_json: dict, output_json: object, *, started: float):
        if len(tool_calls) >= 60:
            return
        tool_calls.append(
            {
                "tool": tool,
                "input": redact_obj(input_json),
                "output": redact_obj(output_json),
                "latency_ms": int((time.perf_counter() - started) * 1000),
            }
        )

    center = GeoPoint(lat=48.8566, lon=2.3522)
    if plan.options and plan.options[0].stay and "location" in trip.get("preferences", {}):
        loc = trip["preferences"]["location"]
        if isinstance(loc, dict) and "lat" in loc and "lon" in loc:
            center = GeoPoint(lat=float(loc["lat"]), lon=float(loc["lon"]))

    poi_payload = {"destination": trip["destination"], "center": {"lat": center.lat, "lon": center.lon}, "limit": 50}

    async def fetch_poi():
        started = time.perf_counter()
        pois = await poi_provider.search(destination=trip["destination"], center=center, limit=50)
        out = [{"id": p.id, "name": p.name, "location": {"lat": p.location.lat, "lon": p.location.lon}} for p in pois]
        record(type(poi_provider).__name__ + ".search", poi_payload, {"count": len(out), "items": out[:3]}, started=started)
        return out

    poi_raw = await _cached(redis, key=_cache_key("poi", poi_payload), ttl_seconds=60 * 60, fn=fetch_poi)
    pois: list[PoiCandidate] = [PoiCandidate(id=p["id"], name=p["name"], location=GeoPoint(**p["location"])) for p in poi_raw]

    start_date = trip["start_date"].isoformat() if isinstance(trip["start_date"], dt.date) else str(trip["start_date"])
    end_date = trip["end_date"].isoformat() if isinstance(trip["end_date"], dt.date) else str(trip["end_date"])
    started = time.perf_counter()
    weather = await weather_provider.forecast(center=center, start_date=start_date, end_date=end_date)
    record(
        type(weather_provider).__name__ + ".forecast",
        {"center": {"lat": center.lat, "lon": center.lon}, "start_date": start_date, "end_date": end_date},
        {"count": len(weather), "items": [w.__dict__ for w in weather[:3]]},
        started=started,
    )
    weather_map = {w.date: w.summary for w in weather}

    dates = trip_days(dt.date.fromisoformat(start_date), dt.date.fromisoformat(end_date))
    periods = ["morning", "afternoon", "evening"]
    per_day = []
    idx = 0
    last_point = center

    for d in dates:
        items: list[ItineraryItem] = []
        weather_summary = weather_map.get(d.isoformat(), "Forecast unavailable")
        for period in periods:
            poi = pois[idx % max(1, len(pois))] if pois else PoiCandidate(id="poi", name="Free exploration", location=center)
            started = time.perf_counter()
            est = await routing_provider.estimate(from_point=last_point, to_point=poi.location, mode="transit")
            record(
                type(routing_provider).__name__ + ".estimate",
                {"from": {"lat": last_point.lat, "lon": last_point.lon}, "to": {"lat": poi.location.lat, "lon": poi.location.lon}, "mode": "transit"},
                est.__dict__,
                started=started,
            )
            items.append(
                ItineraryItem(
                    period=period,
                    poi_name=poi.name,
                    stay_minutes=90 if period != "evening" else 120,
                    commute=Commute(mode="transit" if est.mode != "estimate" else "estimate", minutes=int(est.minutes)),
                    weather_summary=weather_summary,
                )
            )
            last_point = poi.location
            idx += 1
        per_day.append(ItineraryDay(date=d, items=items))

    itinerary = ItineraryJson(generated_at=dt.datetime.now(dt.timezone.utc), plan_index=plan_index, days=per_day)
    issues = verify_itinerary(itinerary=itinerary)
    if issues:
        for day in itinerary.days:
            for item in day.items:
                item.weather_summary = item.weather_summary + " | Note: schedule is tight; consider removing some items"
        issues2 = verify_itinerary(itinerary=itinerary)
        if issues2:
            pass

    md = render_itinerary_markdown(trip=trip, plan=plan, plan_index=plan_index, itinerary=itinerary)
    return itinerary, md, tool_calls


def _explain(label: str, cost_score: float, time_score: float, comfort_score: float, warnings: list[str]) -> str:
    tag = {"cheap": "More budget-focused", "fast": "More time-focused", "balanced": "More balanced"}[label]
    core = f"{tag}. Scores: cost {cost_score:.0f}/100, time {time_score:.0f}/100, comfort {comfort_score:.0f}/100."
    if warnings:
        return core + " Risks: " + "; ".join(warnings)
    return core


def render_plans_markdown(*, trip: dict, plans: PlansJson) -> str:
    lines: list[str] = []
    lines.append("# TripSmith Plans\n")
    lines.append(f"- {trip['origin']} → {trip['destination']}\n")
    lines.append(f"- Dates: {trip['start_date']} ~ {trip['end_date']}\n")
    lines.append(f"- Budget: {trip['budget_total']} {trip['currency']}, travelers: {trip['travelers']}\n")
    lines.append("\n## 3 Options\n")
    for opt in plans.options:
        lines.append(f"### {opt.title}\n")
        lines.append(f"- Total: {opt.metrics.total_price.amount:.0f} {opt.metrics.total_price.currency}\n")
        lines.append(f"- Flight: {opt.flight.depart_at} → {opt.flight.arrive_at}, transfers {opt.flight.stops}, {opt.flight.duration_minutes} min\n")
        lines.append(f"- Stay: {opt.stay.area}, {opt.stay.nightly_price.amount:.0f} {opt.stay.nightly_price.currency}/night\n")
        lines.append(f"- Explanation: {opt.explanation}\n")
        if opt.warnings:
            lines.append("- Notes: " + "; ".join(opt.warnings) + "\n")
        lines.append("\n")
    return "".join(lines)


def render_itinerary_markdown(*, trip: dict, plan: PlansJson, plan_index: int, itinerary: ItineraryJson) -> str:
    opt = plan.options[plan_index]
    lines: list[str] = []
    lines.append("# TripSmith Itinerary\n")
    lines.append(f"- Plan: {opt.title}\n")
    lines.append(f"- Total: {opt.metrics.total_price.amount:.0f} {opt.metrics.total_price.currency}\n\n")
    for day in itinerary.days:
        lines.append(f"## {day.date.isoformat()}\n")
        for item in day.items:
            lines.append(
                f"- {item.period}: {item.poi_name} (stay {item.stay_minutes} min, commute {item.commute.minutes} min, weather: {item.weather_summary})\n"
            )
        lines.append("\n")
    lines.append("\n## Export\n")
    lines.append(f"- ICS: {trip.get('id','')}/export/ics\n")
    lines.append(f"- Markdown: {trip.get('id','')}/export/md\n")
    return "".join(lines)

