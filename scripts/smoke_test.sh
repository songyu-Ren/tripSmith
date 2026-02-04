#!/usr/bin/env bash
set -euo pipefail

dc() {
  if command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    docker compose "$@"
  fi
}

wait_health() {
  local url="$1"
  local deadline=$((SECONDS + 120))
  while [ $SECONDS -lt $deadline ]; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  return 1
}

echo "[smoke] docker compose up -d"
dc up -d

echo "[smoke] wait api health"
wait_health "http://localhost:8000/api/health"

echo "[smoke] run demo seed"
seed_out="$(dc exec -T api python scripts/demo_seed.py)"
echo "$seed_out"
trip_id="$(echo "$seed_out" | tail -n 1 | sed -n 's/^TRIP_ID=//p')"
if [ -z "${trip_id:-}" ]; then
  echo "[smoke] failed to read TRIP_ID" >&2
  exit 2
fi

echo "[smoke] validate ICS parse"
PYTHONPATH="$(pwd)/apps/api" python - "$trip_id" <<'PY'
import os
import sys
import time

import httpx

from tripsmith.schemas.itinerary import ItineraryJson
from tripsmith.schemas.trip_bundle import TripGetResponse

trip_id = os.environ.get("TRIP_ID") or sys.argv[1]
api = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")
user_id = "demo_user"

with httpx.Client(timeout=30) as client:
    trip_bundle = client.get(f"{api}/api/trips/{trip_id}", headers={"X-User-Id": user_id})
    trip_bundle.raise_for_status()
    TripGetResponse.model_validate(trip_bundle.json())
    if not trip_bundle.json().get("latest_plans_json"):
        print("latest_plans_json missing", file=sys.stderr)
        sys.exit(2)

    it_job = client.post(f"{api}/api/trips/{trip_id}/itinerary", json={"plan_index": 2}, headers={"X-User-Id": user_id})
    it_job.raise_for_status()
    job_id = it_job.json()["job_id"]
    deadline = time.time() + 120
    while time.time() < deadline:
        j = client.get(f"{api}/api/jobs/{job_id}", headers={"X-User-Id": user_id})
        j.raise_for_status()
        jb = j.json()
        if jb.get("status") == "succeeded":
            rj = jb.get("result_json") or {}
            ItineraryJson.model_validate(rj.get("itinerary_json"))
            break
        if jb.get("status") == "failed":
            print("itinerary job failed", jb, file=sys.stderr)
            sys.exit(3)
        time.sleep(1)
    else:
        print("itinerary job timeout", file=sys.stderr)
        sys.exit(3)

    ics = client.get(f"{api}/api/trips/{trip_id}/export/ics", headers={"X-User-Id": user_id})
    ics.raise_for_status()
    text = ics.text
    if "BEGIN:VCALENDAR" not in text or "BEGIN:VEVENT" not in text:
        print("ICS missing VCALENDAR/VEVENT", file=sys.stderr)
        sys.exit(3)
    for r in ["DTSTART", "DTEND", "SUMMARY", "UID"]:
        if r not in text:
            print(f"ICS missing field: {r}", file=sys.stderr)
            sys.exit(4)

print("PASS")
PY
