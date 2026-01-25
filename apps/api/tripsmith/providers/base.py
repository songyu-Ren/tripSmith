from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GeoPoint:
    lat: float
    lon: float


@dataclass(frozen=True)
class FlightCandidate:
    id: str
    depart_at: str
    arrive_at: str
    stops: int
    duration_minutes: int
    price_amount: float
    currency: str


@dataclass(frozen=True)
class StayCandidate:
    id: str
    name: str
    area: str
    location: GeoPoint
    nightly_price_amount: float
    total_price_amount: float
    currency: str


@dataclass(frozen=True)
class PoiCandidate:
    id: str
    name: str
    location: GeoPoint


@dataclass(frozen=True)
class WeatherDay:
    date: str
    summary: str


@dataclass(frozen=True)
class RouteEstimate:
    mode: str
    minutes: int


class FlightsProvider:
    async def search(self, *, origin: str, destination: str, start_date: str, end_date: str, travelers: int) -> list[FlightCandidate]:
        raise NotImplementedError


class StaysProvider:
    async def search(self, *, destination: str, start_date: str, end_date: str, travelers: int, budget_total: float) -> list[StayCandidate]:
        raise NotImplementedError


class PoiProvider:
    async def search(self, *, destination: str, center: GeoPoint, limit: int) -> list[PoiCandidate]:
        raise NotImplementedError


class WeatherProvider:
    async def forecast(self, *, center: GeoPoint, start_date: str, end_date: str) -> list[WeatherDay]:
        raise NotImplementedError


class RoutingProvider:
    async def estimate(self, *, from_point: GeoPoint, to_point: GeoPoint, mode: str) -> RouteEstimate:
        raise NotImplementedError

