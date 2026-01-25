from __future__ import annotations

import datetime as dt

from fastapi import Depends
from fastapi import FastAPI
from fastapi import Header
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import PlainTextResponse
from fastapi.requests import Request
from redis import Redis
from sqlalchemy.orm import Session

from tripsmith.agent.orchestrator import generate_itinerary
from tripsmith.agent.orchestrator import generate_plans
from tripsmith.core.config import settings
from tripsmith.core.db import get_db
from tripsmith.core.ids import new_id
from tripsmith.core.rate_limit import check_rate_limit
from tripsmith.core.redis_client import get_redis
from tripsmith.core.sanitize import sanitize_text
from tripsmith.exports.ics import to_ics
from tripsmith.models.alert import Alert
from tripsmith.models.itinerary import Itinerary
from tripsmith.models.plan import Plan
from tripsmith.models.trip import Trip
from tripsmith.schemas.alerts import AlertCreateRequest
from tripsmith.schemas.alerts import AlertCreateResponse
from tripsmith.schemas.alerts import AlertDto
from tripsmith.schemas.itinerary import ItineraryCreateRequest
from tripsmith.schemas.itinerary import ItineraryCreateResponse
from tripsmith.schemas.plan import PlanCreateResponse
from tripsmith.schemas.trip_bundle import TripGetResponse
from tripsmith.schemas.trips import TripCreateRequest
from tripsmith.schemas.trips import TripDto


def redis_dep() -> Redis:
    return get_redis()


def create_app() -> FastAPI:
    docs_url = None if settings.disable_docs else "/docs"
    redoc_url = None if settings.disable_docs else "/redoc"
    app = FastAPI(title="TripSmith API", version="0.1.0", docs_url=docs_url, redoc_url=redoc_url)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.web_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail, headers=getattr(exc, "headers", None))
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": "http_error", "message": str(exc.detail)}},
            headers=getattr(exc, "headers", None),
        )

    def trip_to_dict(trip: Trip) -> dict:
        return {
            "id": trip.id,
            "user_id": trip.user_id,
            "created_at": trip.created_at,
            "origin": trip.origin,
            "destination": trip.destination,
            "start_date": trip.start_date,
            "end_date": trip.end_date,
            "flexible_days": trip.flexible_days,
            "budget_total": float(trip.budget_total),
            "currency": trip.currency,
            "travelers": trip.travelers,
            "preferences": trip.preferences or {},
        }


    @app.get("/api/health")
    def health():
        return {"ok": True, "ts": dt.datetime.now(dt.timezone.utc).isoformat()}

    @app.post("/api/trips", response_model=TripDto)
    def create_trip(
        payload: TripCreateRequest,
        db: Session = Depends(get_db),
        x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    ):
        user_id = sanitize_text(x_user_id or "anonymous")
        if payload.end_date < payload.start_date:
            raise HTTPException(status_code=400, detail={"error": {"code": "bad_dates", "message": "end_date must be >= start_date"}})
        trip = Trip(
            id=new_id(),
            user_id=user_id,
            created_at=dt.datetime.now(dt.timezone.utc),
            origin=sanitize_text(payload.origin),
            destination=sanitize_text(payload.destination),
            start_date=payload.start_date,
            end_date=payload.end_date,
            flexible_days=int(payload.flexible_days),
            budget_total=float(payload.budget_total),
            currency=sanitize_text(payload.currency or "USD"),
            travelers=int(payload.travelers),
            preferences=payload.preferences or {},
        )
        db.add(trip)
        db.commit()
        return TripDto.model_validate(trip)

    @app.get("/api/trips/{trip_id}", response_model=TripGetResponse)
    def get_trip(
        trip_id: str,
        db: Session = Depends(get_db),
        x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    ):
        user_id = sanitize_text(x_user_id or "anonymous")
        trip: Trip | None = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "trip not found"}})
        plan: Plan | None = (
            db.query(Plan).filter(Plan.trip_id == trip_id).order_by(Plan.created_at.desc()).first()
        )
        trip_dto = TripDto.model_validate(trip)
        if not plan:
            return TripGetResponse(trip=trip_dto, latest_plan_id=None, latest_plans_json=None, latest_explain_md=None)
        from tripsmith.schemas.plan import PlansJson

        return TripGetResponse(
            trip=trip_dto,
            latest_plan_id=plan.id,
            latest_plans_json=PlansJson.model_validate(plan.plans_json),
            latest_explain_md=plan.explain_md,
        )

    @app.post("/api/trips/{trip_id}/plan", response_model=PlanCreateResponse)
    async def create_plan(
        trip_id: str,
        db: Session = Depends(get_db),
        x_user_id: str | None = Header(default=None, alias="X-User-Id"),
        redis: Redis = Depends(redis_dep),
    ):
        user_id = sanitize_text(x_user_id or "anonymous")
        trip: Trip | None = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "trip not found"}})

        rl = check_rate_limit(redis, user_id=user_id, route="plan", limit_per_minute=settings.rate_limit_per_minute)
        if not rl.allowed:
            raise HTTPException(
                status_code=429,
                detail={"error": {"code": "rate_limited", "message": "Too many requests"}},
                headers={"Retry-After": str(rl.retry_after_seconds)},
            )

        plans, explain_md = await generate_plans(redis=redis, trip=trip_to_dict(trip))
        plan_row = Plan(
            id=new_id(),
            trip_id=trip_id,
            created_at=dt.datetime.now(dt.timezone.utc),
            plans_json=plans.model_dump(mode="json"),
            explain_md=explain_md,
        )
        db.add(plan_row)
        db.commit()
        return PlanCreateResponse(plan_id=plan_row.id, plans_json=plans, explain_md=explain_md)

    @app.post("/api/trips/{trip_id}/itinerary", response_model=ItineraryCreateResponse)
    async def create_itinerary(
        trip_id: str,
        payload: ItineraryCreateRequest,
        db: Session = Depends(get_db),
        x_user_id: str | None = Header(default=None, alias="X-User-Id"),
        redis: Redis = Depends(redis_dep),
    ):
        user_id = sanitize_text(x_user_id or "anonymous")
        trip: Trip | None = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "trip not found"}})
        plan: Plan | None = (
            db.query(Plan).filter(Plan.trip_id == trip_id).order_by(Plan.created_at.desc()).first()
        )
        if not plan:
            raise HTTPException(status_code=400, detail={"error": {"code": "no_plan", "message": "plan required"}})
        from tripsmith.schemas.plan import PlansJson

        plans_json = PlansJson.model_validate(plan.plans_json)
        if payload.plan_index >= len(plans_json.options):
            raise HTTPException(status_code=400, detail={"error": {"code": "bad_plan_index", "message": "plan_index out of range"}})

        rl = check_rate_limit(redis, user_id=user_id, route="itinerary", limit_per_minute=settings.rate_limit_per_minute)
        if not rl.allowed:
            raise HTTPException(
                status_code=429,
                detail={"error": {"code": "rate_limited", "message": "Too many requests"}},
                headers={"Retry-After": str(rl.retry_after_seconds)},
            )

        itinerary_json, itinerary_md = await generate_itinerary(
            redis=redis, trip=trip_to_dict(trip), plan=plans_json, plan_index=payload.plan_index
        )
        it_row = Itinerary(
            id=new_id(),
            trip_id=trip_id,
            plan_index=int(payload.plan_index),
            created_at=dt.datetime.now(dt.timezone.utc),
            itinerary_json=itinerary_json.model_dump(mode="json"),
            itinerary_md=itinerary_md,
        )
        db.add(it_row)
        db.commit()
        return ItineraryCreateResponse(
            itinerary_id=it_row.id,
            itinerary_json=itinerary_json,
            itinerary_md=itinerary_md,
        )

    @app.get("/api/trips/{trip_id}/export/ics", response_class=PlainTextResponse)
    def export_ics(
        trip_id: str,
        db: Session = Depends(get_db),
        x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    ):
        user_id = sanitize_text(x_user_id or "anonymous")
        trip: Trip | None = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "trip not found"}})
        it: Itinerary | None = db.query(Itinerary).filter(Itinerary.trip_id == trip_id).order_by(Itinerary.created_at.desc()).first()
        if not it:
            raise HTTPException(status_code=400, detail={"error": {"code": "no_itinerary", "message": "itinerary required"}})
        from tripsmith.schemas.itinerary import ItineraryJson

        ics = to_ics(trip_id=trip_id, itinerary=ItineraryJson.model_validate(it.itinerary_json))
        return PlainTextResponse(content=ics, media_type="text/calendar")

    @app.get("/api/trips/{trip_id}/export/md", response_class=PlainTextResponse)
    def export_md(
        trip_id: str,
        db: Session = Depends(get_db),
        x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    ):
        user_id = sanitize_text(x_user_id or "anonymous")
        trip: Trip | None = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "trip not found"}})
        it: Itinerary | None = db.query(Itinerary).filter(Itinerary.trip_id == trip_id).order_by(Itinerary.created_at.desc()).first()
        if not it:
            raise HTTPException(status_code=400, detail={"error": {"code": "no_itinerary", "message": "itinerary required"}})
        return PlainTextResponse(content=it.itinerary_md, media_type="text/markdown")

    @app.post("/api/alerts", response_model=AlertCreateResponse)
    def create_alert(
        payload: AlertCreateRequest,
        db: Session = Depends(get_db),
        x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    ):
        user_id = sanitize_text(x_user_id or "anonymous")
        trip: Trip | None = db.query(Trip).filter(Trip.id == payload.trip_id, Trip.user_id == user_id).first()
        if not trip:
            raise HTTPException(status_code=404, detail={"error": {"code": "not_found", "message": "trip not found"}})
        alert = Alert(
            id=new_id(),
            trip_id=payload.trip_id,
            type=payload.type,
            threshold=float(payload.threshold),
            frequency_minutes=int(payload.frequency_minutes),
            last_checked_at=None,
            is_active=True,
        )
        db.add(alert)
        db.commit()
        dto = AlertDto(
            id=alert.id,
            trip_id=alert.trip_id,
            type=alert.type,
            threshold=float(alert.threshold),
            frequency_minutes=int(alert.frequency_minutes),
            last_checked_at=alert.last_checked_at,
            is_active=bool(alert.is_active),
        )
        return AlertCreateResponse(alert=dto)

    return app


app = create_app()

