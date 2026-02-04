from __future__ import annotations

import datetime as dt

from tripsmith.core.config import settings


def test_rate_limit_returns_429(client):
    old = settings.rate_limit_per_minute
    settings.rate_limit_per_minute = 1
    try:
        p = {
            "origin": "SFO",
            "destination": "PAR",
            "start_date": dt.date(2030, 1, 1).isoformat(),
            "end_date": dt.date(2030, 1, 3).isoformat(),
            "flexible_days": 0,
            "budget_total": 1200,
            "currency": "USD",
            "travelers": 1,
            "preferences": {},
        }
        trip = client.post("/api/trips", json=p, headers={"X-User-Id": "u"}).json()
        trip_id = trip["id"]
        c = client.post(f"/api/trips/{trip_id}/constraints/generate", headers={"X-User-Id": "u"}).json()
        client.put(f"/api/trips/{trip_id}/constraints", json={"constraints": c["constraints"]}, headers={"X-User-Id": "u"})
        resp1 = client.post(f"/api/trips/{trip_id}/plan", headers={"X-User-Id": "u"})
        resp2 = client.post(f"/api/trips/{trip_id}/plan", headers={"X-User-Id": "u"})
        assert resp1.status_code == 200
        assert resp2.status_code == 429
    finally:
        settings.rate_limit_per_minute = old

