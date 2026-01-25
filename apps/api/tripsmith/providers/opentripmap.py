from __future__ import annotations

import httpx

from tripsmith.providers.base import GeoPoint
from tripsmith.providers.base import PoiCandidate


class OpenTripMapPoiProvider:
    def __init__(self, *, api_key: str):
        self.api_key = api_key

    async def search(self, *, destination: str, center: GeoPoint, limit: int) -> list[PoiCandidate]:
        url = "https://api.opentripmap.com/0.1/en/places/radius"
        params = {
            "radius": 6000,
            "lon": center.lon,
            "lat": center.lat,
            "limit": min(limit, 50),
            "apikey": self.api_key,
            "format": "json",
            "rate": "2",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        results: list[PoiCandidate] = []
        for item in data:
            xid = item.get("xid")
            name = item.get("name") or "POI"
            point = item.get("point") or {}
            lat = float(point.get("lat") or center.lat)
            lon = float(point.get("lon") or center.lon)
            if not xid:
                continue
            results.append(PoiCandidate(id=str(xid), name=str(name), location=GeoPoint(lat=lat, lon=lon)))
        return results

