from __future__ import annotations

from tripsmith.providers.base import FlightCandidate


class AmadeusFlightsProvider:
    async def search(self, *, origin: str, destination: str, start_date: str, end_date: str, travelers: int) -> list[FlightCandidate]:
        raise NotImplementedError("Amadeus provider is a stub; enable mock or implement credentials flow")

