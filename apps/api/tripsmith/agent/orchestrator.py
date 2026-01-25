from __future__ import annotations

import datetime as dt
import hashlib
import json

from redis import Redis

from tripsmith.agent.optimizer import choose_plans
from tripsmith.agent.optimizer import compute_scores
from tripsmith.agent.verifier import trip_days
from tripsmith.agent.verifier import verify_itinerary
from tripsmith.agent.verifier import verify_plans
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


async def generate_plans(*, redis: Redis, trip: dict) -> tuple[PlansJson, str]:
    flights_provider = get_flights_provider()
    stays_provider = get_stays_provider()
    routing_provider = get_routing_provider()

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
        results = await flights_provider.search(**flights_payload)
        return [r.__dict__ for r in results]

    async def fetch_stays():
        results = await stays_provider.search(**stays_payload)
        return [
            {
                **r.__dict__,
                "location": {"lat": r.location.lat, "lon": r.location.lon},
            }
            for r in results
        ]

    flights_raw = await _cached(redis, key=_cache_key("flights", flights_payload), ttl_seconds=60 * 30, fn=fetch_flights)
    stays_raw = await _cached(redis, key=_cache_key("stays", stays_payload), ttl_seconds=60 * 30, fn=fetch_stays)

    from tripsmith.providers.base import FlightCandidate
    from tripsmith.providers.base import StayCandidate

    flights = [FlightCandidate(**f) for f in flights_raw][:20]
    stays = [StayCandidate(**{**s, "location": GeoPoint(**s["location"])}) for s in stays_raw][:20]

    commute_est = await routing_provider.estimate(from_point=_to_geo(stays[0].location), to_point=_to_geo(stays[1].location), mode="transit")
    daily_commute_est = int(commute_est.minutes)

    chosen = choose_plans(flights=flights, stays=stays, budget_total=float(trip["budget_total"]), daily_commute_minutes_estimate=daily_commute_est)
    options: list[PlanOption] = []
    for label in ("cheap", "fast", "balanced"):
        c = chosen[label]
        total_cost = float(c.flight.price_amount) + float(c.stay.total_price_amount)
        cost_score, time_score, comfort_score = compute_scores(
            total_cost=total_cost,
            budget_total=float(trip["budget_total"]),
            flight_minutes=int(c.flight.duration_minutes),
            stops=int(c.flight.stops),
            commute_minutes=int(c.daily_commute_minutes_estimate),
        )
        warnings: list[str] = []
        if total_cost > float(trip["budget_total"]):
            warnings.append("预算可能不足；此方案会超出预算")
        if c.flight.stops >= 2:
            warnings.append("转机较多；注意签证/行李衔接")
        options.append(
            PlanOption(
                label=label,
                title={"cheap": "省钱方案", "fast": "省时间方案", "balanced": "平衡方案"}[label],
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
                scores=PlanScores(cost_score=cost_score, time_score=time_score, comfort_score=comfort_score),
                explanation=_explain(label, cost_score, time_score, comfort_score, warnings),
                warnings=warnings,
            )
        )

    plans = PlansJson(generated_at=dt.datetime.now(dt.timezone.utc), options=options)
    issues = verify_plans(trip_budget=float(trip["budget_total"]), plans=plans)
    if issues:
        for opt in plans.options:
            if opt.metrics.total_price.amount > float(trip["budget_total"]):
                opt.warnings.append("系统自检：预算约束无法满足，已输出最接近方案")

    explain_md = render_plans_markdown(trip=trip, plans=plans)
    return plans, explain_md


async def generate_itinerary(*, redis: Redis, trip: dict, plan: PlansJson, plan_index: int) -> tuple[ItineraryJson, str]:
    poi_provider = get_poi_provider()
    weather_provider = get_weather_provider()
    routing_provider = get_routing_provider()

    center = GeoPoint(lat=48.8566, lon=2.3522)
    if plan.options and plan.options[0].stay and "location" in trip.get("preferences", {}):
        loc = trip["preferences"]["location"]
        if isinstance(loc, dict) and "lat" in loc and "lon" in loc:
            center = GeoPoint(lat=float(loc["lat"]), lon=float(loc["lon"]))

    poi_payload = {"destination": trip["destination"], "center": {"lat": center.lat, "lon": center.lon}, "limit": 50}

    async def fetch_poi():
        pois = await poi_provider.search(destination=trip["destination"], center=center, limit=50)
        return [{"id": p.id, "name": p.name, "location": {"lat": p.location.lat, "lon": p.location.lon}} for p in pois]

    poi_raw = await _cached(redis, key=_cache_key("poi", poi_payload), ttl_seconds=60 * 60, fn=fetch_poi)
    pois: list[PoiCandidate] = [PoiCandidate(id=p["id"], name=p["name"], location=GeoPoint(**p["location"])) for p in poi_raw]

    start_date = trip["start_date"].isoformat() if isinstance(trip["start_date"], dt.date) else str(trip["start_date"])
    end_date = trip["end_date"].isoformat() if isinstance(trip["end_date"], dt.date) else str(trip["end_date"])
    weather = await weather_provider.forecast(center=center, start_date=start_date, end_date=end_date)
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
            est = await routing_provider.estimate(from_point=last_point, to_point=poi.location, mode="transit")
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
                item.weather_summary = item.weather_summary + " | 注意：行程偏紧，建议适当删减"
        issues2 = verify_itinerary(itinerary=itinerary)
        if issues2:
            pass

    md = render_itinerary_markdown(trip=trip, plan=plan, plan_index=plan_index, itinerary=itinerary)
    return itinerary, md


def _explain(label: str, cost_score: float, time_score: float, comfort_score: float, warnings: list[str]) -> str:
    tag = {"cheap": "更偏省钱", "fast": "更偏省时", "balanced": "更偏均衡"}[label]
    core = f"{tag}。评分：成本 {cost_score:.0f}/100，时间 {time_score:.0f}/100，舒适 {comfort_score:.0f}/100。"
    if warnings:
        return core + " 风险：" + "；".join(warnings)
    return core


def render_plans_markdown(*, trip: dict, plans: PlansJson) -> str:
    lines: list[str] = []
    lines.append("# TripSmith 方案\n")
    lines.append(f"- {trip['origin']} → {trip['destination']}\n")
    lines.append(f"- 日期：{trip['start_date']} ~ {trip['end_date']}\n")
    lines.append(f"- 预算：{trip['budget_total']} {trip['currency']}，人数：{trip['travelers']}\n")
    lines.append("\n## 3 套方案\n")
    for opt in plans.options:
        lines.append(f"### {opt.title}\n")
        lines.append(f"- 总价：{opt.metrics.total_price.amount:.0f} {opt.metrics.total_price.currency}\n")
        lines.append(f"- 航班：{opt.flight.depart_at} → {opt.flight.arrive_at}，转机 {opt.flight.stops} 次，{opt.flight.duration_minutes} 分钟\n")
        lines.append(f"- 住宿：{opt.stay.area}，{opt.stay.nightly_price.amount:.0f}/{opt.stay.nightly_price.currency} 每晚\n")
        lines.append(f"- 解释：{opt.explanation}\n")
        if opt.warnings:
            lines.append("- 提示：" + "；".join(opt.warnings) + "\n")
        lines.append("\n")
    return "".join(lines)


def render_itinerary_markdown(*, trip: dict, plan: PlansJson, plan_index: int, itinerary: ItineraryJson) -> str:
    opt = plan.options[plan_index]
    lines: list[str] = []
    lines.append("# TripSmith 行程\n")
    lines.append(f"- 方案：{opt.title}\n")
    lines.append(f"- 总价：{opt.metrics.total_price.amount:.0f} {opt.metrics.total_price.currency}\n\n")
    for day in itinerary.days:
        lines.append(f"## {day.date.isoformat()}\n")
        for item in day.items:
            lines.append(
                f"- {item.period}：{item.poi_name}（停留 {item.stay_minutes} 分钟，通勤 {item.commute.minutes} 分钟，天气：{item.weather_summary}）\n"
            )
        lines.append("\n")
    lines.append("\n## 导出\n")
    lines.append(f"- ICS: {trip.get('id','')}/export/ics\n")
    lines.append(f"- Markdown: {trip.get('id','')}/export/md\n")
    return "".join(lines)

