from __future__ import annotations

import datetime as dt
import hashlib
import math
import random

from tripsmith.providers.base import FlightCandidate
from tripsmith.providers.base import GeoPoint
from tripsmith.providers.base import PoiCandidate
from tripsmith.providers.base import RouteEstimate
from tripsmith.providers.base import StayCandidate
from tripsmith.providers.base import WeatherDay


def _seed(*parts: str) -> int:
    h = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return int(h[:8], 16)


class MockFlightsProvider:
    async def search(self, *, origin: str, destination: str, start_date: str, end_date: str, travelers: int) -> list[FlightCandidate]:
        rng = random.Random(_seed("flights", origin, destination, start_date, end_date, str(travelers)))
        base_price = rng.randint(120, 480)
        results: list[FlightCandidate] = []
        for i in range(12):
            stops = rng.choice([0, 0, 1, 1, 2])
            duration = rng.randint(60 * 4, 60 * 16) + stops * rng.randint(30, 120)
            depart = dt.datetime.fromisoformat(f"{start_date}T{rng.randint(6, 20):02d}:00:00")
            arrive = depart + dt.timedelta(minutes=duration)
            price = (base_price + rng.randint(-40, 160) + stops * rng.randint(-10, 30)) * travelers
            results.append(
                FlightCandidate(
                    id=f"mock_f_{i}",
                    depart_at=depart.isoformat(),
                    arrive_at=arrive.isoformat(),
                    stops=stops,
                    duration_minutes=duration,
                    price_amount=float(price),
                    currency="USD",
                )
            )
        return results


class MockStaysProvider:
    async def search(self, *, destination: str, start_date: str, end_date: str, travelers: int, budget_total: float) -> list[StayCandidate]:
        rng = random.Random(_seed("stays", destination, start_date, end_date, str(travelers), str(int(budget_total))))
        start = dt.date.fromisoformat(start_date)
        end = dt.date.fromisoformat(end_date)
        nights = max(1, (end - start).days)
        center = GeoPoint(lat=rng.uniform(48.80, 48.90), lon=rng.uniform(2.25, 2.42))
        areas = ["City Center", "Old Town", "Riverside", "Museum District", "Business Area"]
        results: list[StayCandidate] = []
        for i in range(12):
            area = rng.choice(areas)
            nightly = rng.randint(60, 260)
            total = nightly * nights
            offset_lat = rng.uniform(-0.02, 0.02)
            offset_lon = rng.uniform(-0.03, 0.03)
            results.append(
                StayCandidate(
                    id=f"mock_s_{i}",
                    name=f"Mock Stay {i + 1}",
                    area=area,
                    location=GeoPoint(lat=center.lat + offset_lat, lon=center.lon + offset_lon),
                    nightly_price_amount=float(nightly),
                    total_price_amount=float(total),
                    currency="USD",
                )
            )
        return results


class MockPoiProvider:
    async def search(self, *, destination: str, center: GeoPoint, limit: int) -> list[PoiCandidate]:
        rng = random.Random(_seed("poi", destination, f"{center.lat:.3f}", f"{center.lon:.3f}"))
        base = [
            "Historic Square",
            "City Museum",
            "Local Market",
            "Riverside Walk",
            "Modern Art Gallery",
            "Cathedral",
            "Botanical Garden",
            "Food Street",
            "Viewpoint",
            "Neighborhood Cafe",
        ]
        n = min(limit, 50)
        results: list[PoiCandidate] = []
        for i in range(n):
            name = base[i % len(base)]
            lat = center.lat + rng.uniform(-0.03, 0.03)
            lon = center.lon + rng.uniform(-0.04, 0.04)
            results.append(PoiCandidate(id=f"mock_p_{i}", name=f"{name} {i + 1}", location=GeoPoint(lat=lat, lon=lon)))
        return results


class MockWeatherProvider:
    async def forecast(self, *, center: GeoPoint, start_date: str, end_date: str) -> list[WeatherDay]:
        start = dt.date.fromisoformat(start_date)
        end = dt.date.fromisoformat(end_date)
        days = (end - start).days + 1
        results: list[WeatherDay] = []
        for i in range(days):
            d = start + dt.timedelta(days=i)
            results.append(WeatherDay(date=d.isoformat(), summary="Mild, partly cloudy"))
        return results


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


class MockRoutingProvider:
    async def estimate(self, *, from_point: GeoPoint, to_point: GeoPoint, mode: str) -> RouteEstimate:
        speed = {"walk": 4.5, "drive": 28.0, "transit": 18.0}.get(mode, 12.0)
        minutes = _haversine_minutes(from_point, to_point, speed)
        return RouteEstimate(mode="estimate", minutes=minutes)

