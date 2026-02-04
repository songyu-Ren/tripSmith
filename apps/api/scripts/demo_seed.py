from __future__ import annotations

import datetime as dt
import json
import os
import sys
import time

import httpx


def _wait_job(client: httpx.Client, *, api: str, job_id: str, user_id: str, timeout_seconds: int = 120) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        j = client.get(f"{api}/api/jobs/{job_id}", headers={"X-User-Id": user_id})
        j.raise_for_status()
        body = j.json()
        if body.get("status") in ("succeeded", "failed"):
            return body
        time.sleep(1)
    raise RuntimeError("job timeout")


def main() -> None:
    api = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
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
        trip_resp = client.post(f"{api}/api/trips", json=trip_payload, headers={"X-User-Id": user_id})
        trip_resp.raise_for_status()
        trip = trip_resp.json()
        trip_id = trip["id"]

        constraints_resp = client.post(f"{api}/api/trips/{trip_id}/constraints/generate", headers={"X-User-Id": user_id})
        constraints_resp.raise_for_status()
        constraints = constraints_resp.json()["constraints"]
        confirm_resp = client.put(
            f"{api}/api/trips/{trip_id}/constraints",
            json={"constraints": constraints},
            headers={"X-User-Id": user_id},
        )
        confirm_resp.raise_for_status()

        plan_job = client.post(f"{api}/api/trips/{trip_id}/plan", headers={"X-User-Id": user_id})
        plan_job.raise_for_status()
        plan_job_id = plan_job.json()["job_id"]
        plan_done = _wait_job(client, api=api, job_id=plan_job_id, user_id=user_id)
        if plan_done.get("status") != "succeeded":
            raise RuntimeError(f"plan job failed: {plan_done.get('message')}")
        plan_id = (plan_done.get("result_json") or {}).get("plan_id")

        trip_bundle = client.get(f"{api}/api/trips/{trip_id}", headers={"X-User-Id": user_id})
        trip_bundle.raise_for_status()
        plans_json = trip_bundle.json().get("latest_plans_json")

        it_job = client.post(
            f"{api}/api/trips/{trip_id}/itinerary",
            json={"plan_index": 2},
            headers={"X-User-Id": user_id},
        )
        it_job.raise_for_status()
        it_job_id = it_job.json()["job_id"]
        it_done = _wait_job(client, api=api, job_id=it_job_id, user_id=user_id)
        if it_done.get("status") != "succeeded":
            raise RuntimeError(f"itinerary job failed: {it_done.get('message')}")
        it_result = it_done.get("result_json") or {}
        itinerary_id = it_result.get("itinerary_id")

        alert_resp = client.post(
            f"{api}/api/alerts",
            json={"trip_id": trip_id, "type": "both", "threshold": 220.0, "frequency_minutes": 1},
            headers={"X-User-Id": user_id},
        )
        alert_resp.raise_for_status()

        if "--json" in sys.argv:
            print(
                json.dumps(
                    {
                        "trip_id": trip_id,
                        "plan_id": plan_id,
                        "plans_json": plans_json,
                        "itinerary_id": itinerary_id,
                        "export_ics": f"{api}/api/trips/{trip_id}/export/ics",
                        "export_md": f"{api}/api/trips/{trip_id}/export/md",
                    },
                    ensure_ascii=False,
                )
            )
            return
        print("Trip:", trip_id)
        print("Plan:", plan_id)
        print("Itinerary:", itinerary_id)
        print("ICS:", f"{api}/api/trips/{trip_id}/export/ics")
        print("MD:", f"{api}/api/trips/{trip_id}/export/md")
        print(f"TRIP_ID={trip_id}")


if __name__ == "__main__":
    main()

