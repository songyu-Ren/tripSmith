from __future__ import annotations

import datetime as dt
import hashlib
import asyncio
import os

from celery import Celery
from sqlalchemy.orm import Session

from tripsmith.core.config import settings
from tripsmith.core import db as db_core
from tripsmith.core.errors import ErrorCategory
from tripsmith.core.errors import make_error_code
from tripsmith.core.ids import new_id
from tripsmith.core.logging import log_event
from tripsmith.core.redis_client import get_redis
from tripsmith.models.alert import Alert
from tripsmith.models.itinerary import Itinerary
from tripsmith.models.job import Job
from tripsmith.models.plan import Plan
from tripsmith.models.trip import Trip
from tripsmith.models.notification import Notification


celery_app = Celery(
    "tripsmith",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

if os.getenv("CELERY_ALWAYS_EAGER", "0") == "1":
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True


celery_app.conf.beat_schedule = {
    "refresh-alerts": {
        "task": "tripsmith.refresh_alerts",
        "schedule": 60.0,
    }
}


@celery_app.task(name="tripsmith.refresh_alerts")
def refresh_alerts() -> int:
    db: Session = db_core.SessionLocal()
    try:
        alerts = db.query(Alert).filter(Alert.is_active == True).all()  # noqa: E712
        count = 0
        for alert in alerts:
            if _should_check(alert):
                _check_one(db, alert)
                count += 1
        db.commit()
        return count
    finally:
        db.close()


def _should_check(alert: Alert) -> bool:
    if alert.last_checked_at is None:
        return True
    next_at = alert.last_checked_at + dt.timedelta(minutes=int(alert.frequency_minutes))
    return dt.datetime.now(dt.timezone.utc) >= next_at


def _mock_price(alert: Alert) -> float:
    basis = f"{alert.trip_id}|{alert.type}|{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d-%H')}"
    h = hashlib.sha256(basis.encode("utf-8")).hexdigest()
    return float(int(h[:6], 16) % 500) + 80.0


def _check_one(db: Session, alert: Alert) -> None:
    price = _mock_price(alert)
    alert.last_checked_at = dt.datetime.now(dt.timezone.utc)
    trigger = price <= float(alert.threshold)
    if not trigger:
        return
    payload = {
        "trip_id": alert.trip_id,
        "alert_type": alert.type,
        "price": price,
        "threshold": float(alert.threshold),
        "checked_at": alert.last_checked_at.isoformat(),
    }
    n = Notification(
        id=new_id(),
        alert_id=alert.id,
        created_at=dt.datetime.now(dt.timezone.utc),
        channel="email",
        payload_json=payload,
        status="sent",
    )
    db.add(n)
    log_event("notify_placeholder", alert_id=alert.id, trip_id=alert.trip_id, channel="email", payload=payload)


def _set_step(
    db: Session,
    job: Job,
    *,
    stage: str,
    progress: int,
    message: str,
    result_json: dict | None = None,
) -> None:
    job.stage = stage[:32]
    job.progress = int(progress)
    job.message = message[:256]
    if result_json is not None:
        job.result_json = result_json
    job.updated_at = dt.datetime.now(dt.timezone.utc)
    db.add(job)
    db.commit()


def _fail_job(
    db: Session,
    job: Job,
    *,
    error_code: str,
    error_message: str,
    next_action: str,
) -> None:
    job.status = "failed"
    job.stage = "FAILED"
    job.progress = 100
    job.message = "失败"
    job.error_code = error_code[:64]
    job.error_message = error_message[:256]
    job.next_action = next_action[:256]
    job.updated_at = dt.datetime.now(dt.timezone.utc)
    db.add(job)
    db.commit()


@celery_app.task(name="tripsmith.run_plan_job")
def run_plan_job(job_id: str) -> None:
    from tripsmith.agent.orchestrator import generate_plans

    db: Session = db_core.SessionLocal()
    try:
        job: Job | None = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return
        _set_step(db, job, stage="STARTING", progress=5, message="启动任务")
        job.status = "running"
        db.add(job)
        db.commit()

        trip: Trip | None = db.query(Trip).filter(Trip.id == job.trip_id, Trip.user_id == job.user_id).first()
        if not trip:
            _fail_job(
                db,
                job,
                error_code=make_error_code(ErrorCategory.JOB, "TRIP_NOT_FOUND"),
                error_message="trip not found",
                next_action="返回结果页确认 trip 是否存在，或重新创建行程。",
            )
            return
        if trip.constraints_confirmed_at is None:
            _fail_job(
                db,
                job,
                error_code=make_error_code(ErrorCategory.JOB, "CONSTRAINTS_NOT_CONFIRMED"),
                error_message="constraints not confirmed",
                next_action="先在结果页完成“确认约束”，再重新生成方案。",
            )
            return

        redis = get_redis()
        _set_step(db, job, stage="FETCH_CANDIDATES", progress=20, message="抓取候选数据")

        trip_dict = {
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

        _set_step(db, job, stage="GENERATE", progress=45, message="生成方案")
        plans, explain_md, _tool_calls = asyncio.run(generate_plans(redis=redis, trip=trip_dict))

        _set_step(db, job, stage="VALIDATE", progress=65, message="校验输出")
        if not getattr(plans, "options", None) or len(plans.options) < 3:  # type: ignore[attr-defined]
            _fail_job(
                db,
                job,
                error_code=make_error_code(ErrorCategory.JOB, "PLAN_OUTPUT_INVALID"),
                error_message="plans.options must contain at least 3 options",
                next_action="稍后重试；若持续失败，检查 LLM/Provider 配置或使用 mock provider。",
            )
            return

        _set_step(db, job, stage="PERSIST", progress=80, message="写入数据库")

        plan_row = Plan(
            id=new_id(),
            trip_id=trip.id,
            created_at=dt.datetime.now(dt.timezone.utc),
            plans_json=plans.model_dump(mode="json"),
            explain_md=explain_md,
        )
        db.add(plan_row)
        db.commit()

        _set_step(db, job, stage="COMPLETE", progress=100, message="完成", result_json={"plan_id": plan_row.id})
        job.status = "succeeded"
        job.error_code = None
        job.error_message = None
        job.next_action = None
        db.add(job)
        db.commit()
    except Exception as e:
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                _fail_job(
                    db,
                    job,
                    error_code=make_error_code(ErrorCategory.INTERNAL, "WORKER_EXCEPTION"),
                    error_message=f"{type(e).__name__}: {str(e)}",
                    next_action="稍后重试；若持续失败，检查后台日志并确认 Provider/LLM 配置。",
                )
                log_event(
                    "job_failed",
                    job_id=job.id,
                    job_type=job.type,
                    trip_id=job.trip_id,
                    error_type=type(e).__name__,
                    error_message=str(e),
                )
        finally:
            return
    finally:
        db.close()


@celery_app.task(name="tripsmith.run_itinerary_job")
def run_itinerary_job(job_id: str) -> None:
    from tripsmith.agent.orchestrator import generate_itinerary
    from tripsmith.schemas.plan import PlansJson

    db: Session = db_core.SessionLocal()
    try:
        job: Job | None = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return
        _set_step(db, job, stage="STARTING", progress=5, message="启动任务")
        job.status = "running"
        db.add(job)
        db.commit()

        trip: Trip | None = db.query(Trip).filter(Trip.id == job.trip_id, Trip.user_id == job.user_id).first()
        if not trip:
            _fail_job(
                db,
                job,
                error_code=make_error_code(ErrorCategory.JOB, "TRIP_NOT_FOUND"),
                error_message="trip not found",
                next_action="返回结果页确认 trip 是否存在，或重新创建行程。",
            )
            return
        plan_id = (job.result_json or {}).get("plan_id")
        if isinstance(plan_id, str) and plan_id:
            plan_row = db.query(Plan).filter(Plan.id == plan_id, Plan.trip_id == job.trip_id).first()
        else:
            plan_row = db.query(Plan).filter(Plan.trip_id == job.trip_id).order_by(Plan.created_at.desc()).first()
        if not plan_row:
            _fail_job(
                db,
                job,
                error_code=make_error_code(ErrorCategory.JOB, "PLAN_REQUIRED"),
                error_message="plan required",
                next_action="先生成方案，再生成逐日行程。",
            )
            return

        plan_index = int((job.result_json or {}).get("plan_index", 0))
        plans_json = PlansJson.model_validate(plan_row.plans_json)
        redis = get_redis()

        trip_dict = {
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

        _set_step(db, job, stage="GENERATE", progress=45, message="生成逐日行程")
        itinerary_json, itinerary_md, _tool_calls = asyncio.run(generate_itinerary(redis=redis, trip=trip_dict, plan=plans_json, plan_index=plan_index))

        _set_step(db, job, stage="VALIDATE", progress=65, message="校验输出")
        if not getattr(itinerary_json, "days", None):  # type: ignore[attr-defined]
            _fail_job(
                db,
                job,
                error_code=make_error_code(ErrorCategory.JOB, "ITINERARY_OUTPUT_INVALID"),
                error_message="itinerary.days is empty",
                next_action="稍后重试；若持续失败，尝试更换方案或收紧约束。",
            )
            return

        _set_step(db, job, stage="PERSIST", progress=80, message="写入数据库")

        it_row = Itinerary(
            id=new_id(),
            trip_id=trip.id,
            plan_index=plan_index,
            created_at=dt.datetime.now(dt.timezone.utc),
            itinerary_json=itinerary_json.model_dump(mode="json"),
            itinerary_md=itinerary_md,
        )
        db.add(it_row)
        db.commit()

        _set_step(
            db,
            job,
            stage="COMPLETE",
            progress=100,
            message="完成",
            result_json={
                "itinerary_id": it_row.id,
                "itinerary_json": itinerary_json.model_dump(mode="json"),
                "itinerary_md": itinerary_md,
            },
        )
        job.status = "succeeded"
        job.error_code = None
        job.error_message = None
        job.next_action = None
        db.add(job)
        db.commit()
    except Exception as e:
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                _fail_job(
                    db,
                    job,
                    error_code=make_error_code(ErrorCategory.INTERNAL, "WORKER_EXCEPTION"),
                    error_message=f"{type(e).__name__}: {str(e)}",
                    next_action="稍后重试；若持续失败，检查后台日志并确认 Provider/LLM 配置。",
                )
                log_event(
                    "job_failed",
                    job_id=job.id,
                    job_type=job.type,
                    trip_id=job.trip_id,
                    error_type=type(e).__name__,
                    error_message=str(e),
                )
        finally:
            return
    finally:
        db.close()

