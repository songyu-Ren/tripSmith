from __future__ import annotations

import datetime as dt
import time
import os

from fastapi import Depends
from fastapi import FastAPI
from fastapi import Header
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import PlainTextResponse
from fastapi.requests import Request
from redis import Redis
from sqlalchemy.orm import Session

from tripsmith.agent.intake import generate_constraints
from tripsmith.core.config import cors_origins
from tripsmith.core.config import settings
from tripsmith.core.db import get_db
from tripsmith.core.errors import ApiException
from tripsmith.core.ids import new_id
from tripsmith.core.logging import log_event
from tripsmith.core.rate_limit import check_rate_limit
from tripsmith.core.redis_client import get_redis
from tripsmith.core.sanitize import sanitize_text
from tripsmith.core.sanitize import redact_obj
from tripsmith.exports.ics import to_ics
from tripsmith.models.alert import Alert
from tripsmith.models.agent_run import AgentRun
from tripsmith.models.itinerary import Itinerary
from tripsmith.models.job import Job
from tripsmith.models.plan import Plan
from tripsmith.models.saved_plan import SavedPlan
from tripsmith.models.trip import Trip
from tripsmith.schemas.alerts import AlertCreateRequest
from tripsmith.schemas.alerts import AlertCreateResponse
from tripsmith.schemas.alerts import AlertDto
from tripsmith.schemas.agent_runs import AgentRunDto
from tripsmith.schemas.agent_runs import AgentRunListResponse
from tripsmith.schemas.constraints import ConstraintsGenerateResponse
from tripsmith.schemas.constraints import ConstraintsGetResponse
from tripsmith.schemas.constraints import ConstraintsUpdateRequest
from tripsmith.schemas.itinerary import ItineraryCreateRequest
from tripsmith.schemas.jobs import JobCreateResponse
from tripsmith.schemas.jobs import JobDto
from tripsmith.schemas.saved_plans import SavePlanRequest
from tripsmith.schemas.saved_plans import SavedPlanDto
from tripsmith.schemas.saved_plans import SavePlanResponse
from tripsmith.schemas.saved_plans import SavedPlansListResponse
from tripsmith.schemas.trip_bundle import TripGetResponse
from tripsmith.schemas.trips import TripCreateRequest
from tripsmith.schemas.trips import TripDto


def redis_dep() -> Redis:
    return get_redis()


def create_app() -> FastAPI:
    docs_url = None if settings.disable_docs else "/docs"
    redoc_url = None if settings.disable_docs else "/redoc"
    app = FastAPI(title="TripSmith API", version="0.2.0", docs_url=docs_url, redoc_url=redoc_url)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def _get_request_id(request: Request) -> str:
        rid = getattr(request.state, "request_id", None)
        if isinstance(rid, str) and rid:
            return rid
        return "unknown"

    def _error_response(
        *,
        request: Request,
        status_code: int,
        error_code: str,
        message: str,
        details: object | None = None,
        headers: dict[str, str] | None = None,
    ) -> JSONResponse:
        payload = {"error_code": error_code, "message": message, "request_id": _get_request_id(request)}
        if settings.dev_mode and details is not None:
            payload["details"] = details
        resp = JSONResponse(status_code=status_code, content=payload)
        resp.headers["X-Request-Id"] = _get_request_id(request)
        if headers:
            for k, v in headers.items():
                resp.headers[k] = v
        return resp

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or new_id()
        request.state.request_id = request_id
        started = time.perf_counter()
        response = None
        try:
            response = await call_next(request)
            response.headers["X-Request-Id"] = request_id
            return response
        finally:
            latency_ms = int((time.perf_counter() - started) * 1000)
            user_id = sanitize_text(request.headers.get("x-user-id") or "anonymous")
            trip_id = None
            path = request.url.path
            if "/api/trips/" in path:
                try:
                    trip_id = path.split("/api/trips/", 1)[1].split("/", 1)[0]
                except Exception:
                    trip_id = None
            log_event(
                "http_request",
                request_id=request_id,
                path=path,
                method=request.method,
                latency_ms=latency_ms,
                status_code=getattr(response, "status_code", None) if response is not None else None,
                user_id=user_id,
                trip_id=trip_id,
            )

    @app.exception_handler(ApiException)
    async def api_exception_handler(request: Request, exc: ApiException):
        return _error_response(
            request=request,
            status_code=exc.status_code,
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return _error_response(
            request=request,
            status_code=422,
            error_code="validation_error",
            message="Invalid request",
            details=exc.errors(),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return _error_response(
            request=request,
            status_code=exc.status_code,
            error_code="http_error",
            message=str(exc.detail),
            details={"detail": exc.detail},
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return _error_response(
            request=request,
            status_code=500,
            error_code="internal_error",
            message="Internal server error",
            details={"type": type(exc).__name__, "message": str(exc)},
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
            "constraints": trip.constraints_json,
            "constraints_confirmed_at": trip.constraints_confirmed_at,
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
            raise ApiException(status_code=400, error_code="bad_dates", message="end_date must be >= start_date")
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
            constraints_json=None,
            constraints_confirmed_at=None,
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
            raise ApiException(status_code=404, error_code="not_found", message="trip not found")
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

    @app.get("/api/trips/{trip_id}/constraints", response_model=ConstraintsGetResponse)
    def get_constraints(
        trip_id: str,
        db: Session = Depends(get_db),
        x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    ):
        user_id = sanitize_text(x_user_id or "anonymous")
        trip: Trip | None = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
        if not trip:
            raise ApiException(status_code=404, error_code="not_found", message="trip not found")
        confirmed = trip.constraints_confirmed_at is not None
        return ConstraintsGetResponse(constraints=trip.constraints_json, confirmed=confirmed)

    @app.post("/api/trips/{trip_id}/constraints/generate", response_model=ConstraintsGenerateResponse)
    def generate_trip_constraints(
        trip_id: str,
        db: Session = Depends(get_db),
        x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    ):
        user_id = sanitize_text(x_user_id or "anonymous")
        trip: Trip | None = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
        if not trip:
            raise ApiException(status_code=404, error_code="not_found", message="trip not found")
        constraints = generate_constraints(trip=trip_to_dict(trip))
        trip.constraints_json = constraints.model_dump(mode="json")
        trip.constraints_confirmed_at = None
        db.add(trip)
        db.commit()
        run = AgentRun(
            id=new_id(),
            trip_id=trip_id,
            created_at=dt.datetime.now(dt.timezone.utc),
            phase="intake",
            input_json=redact_obj({"trip": trip_to_dict(trip)}),
            output_json=redact_obj({"constraints": constraints.model_dump(mode="json")}),
            tool_calls_json=[],
            model_info={"provider": settings.llm_provider, "model": "mock", "temperature": 0},
            prompt_version="v0.2.0",
            commit_hash=(settings.commit_hash or "unknown")[:64],
        )
        db.add(run)
        db.commit()
        return ConstraintsGenerateResponse(constraints=constraints)

    @app.put("/api/trips/{trip_id}/constraints", response_model=ConstraintsGetResponse)
    def confirm_constraints(
        trip_id: str,
        payload: ConstraintsUpdateRequest,
        db: Session = Depends(get_db),
        x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    ):
        user_id = sanitize_text(x_user_id or "anonymous")
        trip: Trip | None = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
        if not trip:
            raise ApiException(status_code=404, error_code="not_found", message="trip not found")
        trip.constraints_json = payload.constraints.model_dump(mode="json")
        trip.constraints_confirmed_at = dt.datetime.now(dt.timezone.utc)
        db.add(trip)
        db.commit()
        return ConstraintsGetResponse(constraints=payload.constraints, confirmed=True)

    @app.post("/api/trips/{trip_id}/plan", response_model=JobCreateResponse)
    def create_plan(
        trip_id: str,
        db: Session = Depends(get_db),
        x_user_id: str | None = Header(default=None, alias="X-User-Id"),
        redis: Redis = Depends(redis_dep),
    ):
        user_id = sanitize_text(x_user_id or "anonymous")
        trip: Trip | None = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
        if not trip:
            raise ApiException(status_code=404, error_code="not_found", message="trip not found")
        if trip.constraints_confirmed_at is None:
            raise ApiException(status_code=400, error_code="constraints_not_confirmed", message="constraints must be confirmed first")

        rl = check_rate_limit(redis, user_id=user_id, route="plan", limit_per_minute=settings.rate_limit_per_minute)
        if not rl.allowed:
            raise ApiException(
                status_code=429,
                error_code="rate_limited",
                message="Too many requests",
                details={"retry_after_seconds": rl.retry_after_seconds},
                headers={"Retry-After": str(rl.retry_after_seconds)},
            )

        now = dt.datetime.now(dt.timezone.utc)
        job = Job(
            id=new_id(),
            trip_id=trip_id,
            user_id=user_id,
            type="plan",
            status="queued",
            progress=0,
            message="queued",
            result_json=None,
            created_at=now,
            updated_at=now,
        )
        db.add(job)
        db.commit()

        from tripsmith.worker import run_plan_job
        from tripsmith.worker import celery_app

        if os.getenv("CELERY_ALWAYS_EAGER", "0") == "1":
            celery_app.conf.task_always_eager = True
            celery_app.conf.task_eager_propagates = True

        run_plan_job.delay(job.id)
        return JobCreateResponse(job_id=job.id)

    @app.post("/api/trips/{trip_id}/itinerary", response_model=JobCreateResponse)
    def create_itinerary(
        trip_id: str,
        payload: ItineraryCreateRequest,
        db: Session = Depends(get_db),
        x_user_id: str | None = Header(default=None, alias="X-User-Id"),
        redis: Redis = Depends(redis_dep),
    ):
        user_id = sanitize_text(x_user_id or "anonymous")
        trip: Trip | None = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
        if not trip:
            raise ApiException(status_code=404, error_code="not_found", message="trip not found")
        if payload.plan_id:
            plan = db.query(Plan).filter(Plan.id == payload.plan_id, Plan.trip_id == trip_id).first()
        else:
            plan = db.query(Plan).filter(Plan.trip_id == trip_id).order_by(Plan.created_at.desc()).first()
        if not plan:
            raise ApiException(status_code=400, error_code="no_plan", message="plan required")
        from tripsmith.schemas.plan import PlansJson

        plans_json = PlansJson.model_validate(plan.plans_json)
        if payload.plan_index >= len(plans_json.options):
            raise ApiException(status_code=400, error_code="bad_plan_index", message="plan_index out of range")

        rl = check_rate_limit(redis, user_id=user_id, route="itinerary", limit_per_minute=settings.rate_limit_per_minute)
        if not rl.allowed:
            raise ApiException(
                status_code=429,
                error_code="rate_limited",
                message="Too many requests",
                details={"retry_after_seconds": rl.retry_after_seconds},
                headers={"Retry-After": str(rl.retry_after_seconds)},
            )

        now = dt.datetime.now(dt.timezone.utc)
        job = Job(
            id=new_id(),
            trip_id=trip_id,
            user_id=user_id,
            type="itinerary",
            status="queued",
            progress=0,
            message="queued",
            result_json={"plan_index": int(payload.plan_index), "plan_id": plan.id},
            created_at=now,
            updated_at=now,
        )
        db.add(job)
        db.commit()

        from tripsmith.worker import run_itinerary_job
        from tripsmith.worker import celery_app

        if os.getenv("CELERY_ALWAYS_EAGER", "0") == "1":
            celery_app.conf.task_always_eager = True
            celery_app.conf.task_eager_propagates = True

        run_itinerary_job.delay(job.id)
        return JobCreateResponse(job_id=job.id)

    @app.get("/api/jobs/{job_id}", response_model=JobDto)
    def get_job(
        job_id: str,
        db: Session = Depends(get_db),
        x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    ):
        user_id = sanitize_text(x_user_id or "anonymous")
        job: Job | None = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
        if not job:
            raise ApiException(status_code=404, error_code="not_found", message="job not found")
        return JobDto.model_validate(job)

    @app.get("/api/trips/{trip_id}/saved_plans", response_model=SavedPlansListResponse)
    def list_saved_plans(
        trip_id: str,
        db: Session = Depends(get_db),
        x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    ):
        user_id = sanitize_text(x_user_id or "anonymous")
        trip: Trip | None = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
        if not trip:
            raise ApiException(status_code=404, error_code="not_found", message="trip not found")
        rows: list[SavedPlan] = (
            db.query(SavedPlan)
            .filter(SavedPlan.trip_id == trip_id)
            .order_by(SavedPlan.created_at.desc())
            .all()
        )
        return SavedPlansListResponse(saved_plans=[SavedPlanDto.model_validate(r) for r in rows])

    @app.post("/api/trips/{trip_id}/saved_plans", response_model=SavePlanResponse)
    def save_plan(
        trip_id: str,
        payload: SavePlanRequest,
        db: Session = Depends(get_db),
        x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    ):
        user_id = sanitize_text(x_user_id or "anonymous")
        trip: Trip | None = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
        if not trip:
            raise ApiException(status_code=404, error_code="not_found", message="trip not found")

        plan: Plan | None = db.query(Plan).filter(Plan.id == payload.plan_id, Plan.trip_id == trip_id).first()
        if not plan:
            raise ApiException(status_code=404, error_code="not_found", message="plan not found")

        from tripsmith.schemas.plan import PlansJson

        plans_json = PlansJson.model_validate(plan.plans_json)
        if payload.plan_index >= len(plans_json.options):
            raise ApiException(status_code=400, error_code="bad_plan_index", message="plan_index out of range")

        now = dt.datetime.now(dt.timezone.utc)
        row = SavedPlan(
            id=new_id(),
            trip_id=trip_id,
            plan_id=payload.plan_id,
            plan_index=int(payload.plan_index),
            label=sanitize_text(payload.label),
            created_at=now,
        )
        db.add(row)
        db.commit()
        return SavePlanResponse(saved_plan=SavedPlanDto.model_validate(row))

    @app.get("/api/trips/{trip_id}/export/ics", response_class=PlainTextResponse)
    def export_ics(
        trip_id: str,
        db: Session = Depends(get_db),
        x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    ):
        user_id = sanitize_text(x_user_id or "anonymous")
        trip: Trip | None = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
        if not trip:
            raise ApiException(status_code=404, error_code="not_found", message="trip not found")
        it: Itinerary | None = db.query(Itinerary).filter(Itinerary.trip_id == trip_id).order_by(Itinerary.created_at.desc()).first()
        if not it:
            raise ApiException(status_code=400, error_code="no_itinerary", message="itinerary required")
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
            raise ApiException(status_code=404, error_code="not_found", message="trip not found")
        it: Itinerary | None = db.query(Itinerary).filter(Itinerary.trip_id == trip_id).order_by(Itinerary.created_at.desc()).first()
        if not it:
            raise ApiException(status_code=400, error_code="no_itinerary", message="itinerary required")
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
            raise ApiException(status_code=404, error_code="not_found", message="trip not found")
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

    @app.get("/api/debug/trips/{trip_id}/runs", response_model=AgentRunListResponse)
    def debug_trip_runs(
        trip_id: str,
        db: Session = Depends(get_db),
        x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    ):
        if not settings.dev_mode:
            raise ApiException(status_code=404, error_code="not_found", message="not found")
        user_id = sanitize_text(x_user_id or "anonymous")
        trip: Trip | None = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user_id).first()
        if not trip:
            raise ApiException(status_code=404, error_code="not_found", message="trip not found")
        runs = db.query(AgentRun).filter(AgentRun.trip_id == trip_id).order_by(AgentRun.created_at.desc()).all()
        return AgentRunListResponse(runs=[AgentRunDto.model_validate(r) for r in runs])

    @app.get("/api/debug/runs/{run_id}", response_model=AgentRunDto)
    def debug_run(
        run_id: str,
        db: Session = Depends(get_db),
    ):
        if not settings.dev_mode:
            raise ApiException(status_code=404, error_code="not_found", message="not found")
        run: AgentRun | None = db.query(AgentRun).filter(AgentRun.id == run_id).first()
        if not run:
            raise ApiException(status_code=404, error_code="not_found", message="run not found")
        return AgentRunDto.model_validate(run)

    return app


app = create_app()

