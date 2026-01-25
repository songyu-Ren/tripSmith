from __future__ import annotations

import math

import httpx

from tripsmith.providers.base import GeoPoint
from tripsmith.providers.base import RouteEstimate


class OsrmRoutingProvider:
    def __init__(self, *, base_url: str = "http://router.project-osrm.org"):
        self.base_url = base_url.rstrip("/")

    async def estimate(self, *, from_point: GeoPoint, to_point: GeoPoint, mode: str) -> RouteEstimate:
        profile = "driving" if mode in ("drive", "transit") else "foot"
        url = f"{self.base_url}/route/v1/{profile}/{from_point.lon},{from_point.lat};{to_point.lon},{to_point.lat}"
        params = {"overview": "false"}
        try:
            async with httpx.AsyncClient(timeout=6) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
            routes = data.get("routes") or []
            if not routes:
                raise RuntimeError("no routes")
            duration_s = float(routes[0].get("duration") or 0)
            minutes = max(1, int(round(duration_s / 60)))
            return RouteEstimate(mode=mode, minutes=minutes)
        except Exception:
            minutes = _haversine_minutes(from_point, to_point, _speed_kmh(mode))
            return RouteEstimate(mode="estimate", minutes=minutes)


def _speed_kmh(mode: str) -> float:
    return {"walk": 4.5, "drive": 28.0, "transit": 18.0}.get(mode, 12.0)


def _haversine_minutes(a: GeoPoint, b: GeoPoint, km_per_h: float) -> int:
    r = 6371.0
    lat1 = math.radians(a.lat)
    lat2 = math.radians(b.lat)
    dlat = lat2 - lat1
    dlon = math.radians(b.lon - a.lon)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    km = 2 * r * math.asin(math.sqrt(h))
    minutes = int(round((km / max(1e-6, km_per_h)) * 60))
    return max(1, minutes)

