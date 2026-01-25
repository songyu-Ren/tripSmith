from __future__ import annotations

import datetime as dt

import httpx


def main() -> None:
    api = "http://localhost:8000"
    user_id = "demo_user"

    trip_payload = {
        "origin": "SFO",
        "destination": "PAR",
        "start_date": (dt.date.today() + dt.timedelta(days=30)).isoformat(),
        "end_date": (dt.date.today() + dt.timedelta(days=35)).isoformat(),
        "flexible_days": 2,
        "budget_total": 1800,
        "currency": "USD",
        "travelers": 1,
        "preferences": {"pace": "balanced"},
    }

    with httpx.Client(timeout=30) as client:
        trip = client.post(f"{api}/api/trips", json=trip_payload, headers={"X-User-Id": user_id}).json()
        trip_id = trip["id"]
        plan = client.post(f"{api}/api/trips/{trip_id}/plan", headers={"X-User-Id": user_id}).json()
        it = client.post(
            f"{api}/api/trips/{trip_id}/itinerary",
            json={"plan_index": 2},
            headers={"X-User-Id": user_id},
        ).json()
        client.post(
            f"{api}/api/alerts",
            json={"trip_id": trip_id, "type": "both", "threshold": 220.0, "frequency_minutes": 1},
            headers={"X-User-Id": user_id},
        )
        print("Trip:", trip_id)
        print("Plan:", plan["plan_id"])
        print("Itinerary:", it["itinerary_id"])
        print("ICS:", f"{api}/api/trips/{trip_id}/export/ics")
        print("MD:", f"{api}/api/trips/{trip_id}/export/md")


if __name__ == "__main__":
    main()

