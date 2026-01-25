from __future__ import annotations

from tripsmith.providers.base import FlightCandidate


class DuffelFlightsProvider:
    async def search(self, *, origin: str, destination: str, start_date: str, end_date: str, travelers: int) -> list[FlightCandidate]:
        raise NotImplementedError("Duffel provider is a stub; enable mock or implement credentials flow")

