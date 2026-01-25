from __future__ import annotations

import datetime as dt

import httpx

from tripsmith.providers.base import GeoPoint
from tripsmith.providers.base import WeatherDay


class OpenMeteoWeatherProvider:
    async def forecast(self, *, center: GeoPoint, start_date: str, end_date: str) -> list[WeatherDay]:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": center.lat,
            "longitude": center.lon,
            "daily": "weathercode,temperature_2m_max,temperature_2m_min",
            "timezone": "UTC",
            "start_date": start_date,
            "end_date": end_date,
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            return _fallback_days(start_date=start_date, end_date=end_date)

        daily = data.get("daily") or {}
        times: list[str] = daily.get("time") or []
        codes: list[int] = daily.get("weathercode") or []
        tmax: list[float] = daily.get("temperature_2m_max") or []
        tmin: list[float] = daily.get("temperature_2m_min") or []

        results: list[WeatherDay] = []
        for i, day in enumerate(times):
            code = codes[i] if i < len(codes) else None
            hi = tmax[i] if i < len(tmax) else None
            lo = tmin[i] if i < len(tmin) else None
            summary = _code_to_summary(code)
            if hi is not None and lo is not None:
                summary = f"{summary} ({lo:.0f}°C–{hi:.0f}°C)"
            results.append(WeatherDay(date=day, summary=summary))

        if results:
            return results

        return _fallback_days(start_date=start_date, end_date=end_date)


def _fallback_days(*, start_date: str, end_date: str) -> list[WeatherDay]:
    start = dt.date.fromisoformat(start_date)
    end = dt.date.fromisoformat(end_date)
    days = (end - start).days + 1
    return [WeatherDay(date=(start + dt.timedelta(days=i)).isoformat(), summary="Forecast unavailable") for i in range(days)]


def _code_to_summary(code: int | None) -> str:
    if code is None:
        return "Forecast unavailable"
    if code == 0:
        return "Clear"
    if code in (1, 2, 3):
        return "Partly cloudy"
    if code in (45, 48):
        return "Fog"
    if code in (51, 53, 55):
        return "Drizzle"
    if code in (61, 63, 65):
        return "Rain"
    if code in (71, 73, 75):
        return "Snow"
    if code in (80, 81, 82):
        return "Rain showers"
    if code in (95, 96, 99):
        return "Thunderstorm"
    return "Mixed"

