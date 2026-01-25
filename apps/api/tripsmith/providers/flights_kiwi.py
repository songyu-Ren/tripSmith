from __future__ import annotations

import datetime as dt

import httpx

from tripsmith.providers.base import FlightCandidate


class KiwiTequilaFlightsProvider:
    def __init__(self, *, api_key: str):
        self.api_key = api_key

    async def search(self, *, origin: str, destination: str, start_date: str, end_date: str, travelers: int) -> list[FlightCandidate]:
        url = "https://tequila-api.kiwi.com/v2/search"
        start = dt.date.fromisoformat(start_date)
        params = {
            "fly_from": origin,
            "fly_to": destination,
            "date_from": start.strftime("%d/%m/%Y"),
            "date_to": start.strftime("%d/%m/%Y"),
            "adults": travelers,
            "curr": "USD",
            "limit": 20,
        }
        headers = {"apikey": self.api_key}
        async with httpx.AsyncClient(timeout=12) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        items = data.get("data") or []
        results: list[FlightCandidate] = []
        for i, item in enumerate(items):
            depart = item.get("utc_departure")
            arrive = item.get("utc_arrival")
            duration = int(item.get("duration", {}).get("total") or 0)
            price = float(item.get("price") or 0)
            route = item.get("route") or []
            stops = max(0, len(route) - 1)
            results.append(
                FlightCandidate(
                    id=str(item.get("id") or f"kiwi_{i}"),
                    depart_at=str(depart),
                    arrive_at=str(arrive),
                    stops=stops,
                    duration_minutes=max(1, int(round(duration / 60))),
                    price_amount=price,
                    currency="USD",
                )
            )
        return results

