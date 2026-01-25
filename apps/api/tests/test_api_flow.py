from __future__ import annotations

import datetime as dt


def _trip_payload():
    today = dt.date(2030, 1, 1)
    return {
        "origin": "SFO",
        "destination": "PAR",
        "start_date": today.isoformat(),
        "end_date": (today + dt.timedelta(days=4)).isoformat(),
        "flexible_days": 2,
        "budget_total": 1800,
        "currency": "USD",
        "travelers": 1,
        "preferences": {"tags": ["balanced"]},
    }


def test_health_ok(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_create_trip_validation_bad_dates(client):
    p = _trip_payload()
    p["start_date"] = "2030-01-10"
    p["end_date"] = "2030-01-01"
    resp = client.post("/api/trips", json=p, headers={"X-User-Id": "u"})
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "bad_dates"


def test_plan_generation_returns_three_options(client):
    trip = client.post("/api/trips", json=_trip_payload(), headers={"X-User-Id": "u"}).json()
    trip_id = trip["id"]
    resp = client.post(f"/api/trips/{trip_id}/plan", headers={"X-User-Id": "u"})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["plans_json"]["options"]) >= 3
    labels = [o["label"] for o in body["plans_json"]["options"][:3]]
    assert set(labels) == {"cheap", "fast", "balanced"}


def test_itinerary_generation_structure(client):
    trip = client.post("/api/trips", json=_trip_payload(), headers={"X-User-Id": "u"}).json()
    trip_id = trip["id"]
    client.post(f"/api/trips/{trip_id}/plan", headers={"X-User-Id": "u"})
    resp = client.post(f"/api/trips/{trip_id}/itinerary", json={"plan_index": 0}, headers={"X-User-Id": "u"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["itinerary_json"]["plan_index"] == 0
    assert len(body["itinerary_json"]["days"]) == 5
    assert len(body["itinerary_json"]["days"][0]["items"]) == 3


def test_export_ics_contains_calendar(client):
    trip = client.post("/api/trips", json=_trip_payload(), headers={"X-User-Id": "u"}).json()
    trip_id = trip["id"]
    client.post(f"/api/trips/{trip_id}/plan", headers={"X-User-Id": "u"})
    client.post(f"/api/trips/{trip_id}/itinerary", json={"plan_index": 1}, headers={"X-User-Id": "u"})
    resp = client.get(f"/api/trips/{trip_id}/export/ics", headers={"X-User-Id": "u"})
    assert resp.status_code == 200
    assert "BEGIN:VCALENDAR" in resp.text
    assert "BEGIN:VEVENT" in resp.text


def test_export_md_contains_heading(client):
    trip = client.post("/api/trips", json=_trip_payload(), headers={"X-User-Id": "u"}).json()
    trip_id = trip["id"]
    client.post(f"/api/trips/{trip_id}/plan", headers={"X-User-Id": "u"})
    client.post(f"/api/trips/{trip_id}/itinerary", json={"plan_index": 2}, headers={"X-User-Id": "u"})
    resp = client.get(f"/api/trips/{trip_id}/export/md", headers={"X-User-Id": "u"})
    assert resp.status_code == 200
    assert resp.text.startswith("# TripSmith 行程")

