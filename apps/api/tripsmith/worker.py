from __future__ import annotations

import datetime as dt
import hashlib

from celery import Celery
from sqlalchemy.orm import Session

from tripsmith.core.config import settings
from tripsmith.core.db import SessionLocal
from tripsmith.core.ids import new_id
from tripsmith.models.alert import Alert
from tripsmith.models.notification import Notification


celery_app = Celery(
    "tripsmith",
    broker=settings.redis_url,
    backend=settings.redis_url,
)


celery_app.conf.beat_schedule = {
    "refresh-alerts": {
        "task": "tripsmith.refresh_alerts",
        "schedule": 60.0,
    }
}


@celery_app.task(name="tripsmith.refresh_alerts")
def refresh_alerts() -> int:
    db: Session = SessionLocal()
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
    print(f"[notify] email placeholder: {payload}")

