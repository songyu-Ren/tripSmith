from __future__ import annotations

from tripsmith.providers.base import StayCandidate


class BookingStaysProvider:
    async def search(self, *, destination: str, start_date: str, end_date: str, travelers: int, budget_total: float) -> list[StayCandidate]:
        raise NotImplementedError("Booking Demand API provider is a stub; enable mock")

