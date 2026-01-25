from __future__ import annotations

from dataclasses import dataclass

from tripsmith.providers.base import FlightCandidate
from tripsmith.providers.base import StayCandidate


@dataclass(frozen=True)
class OptimizedChoice:
    flight: FlightCandidate
    stay: StayCandidate
    daily_commute_minutes_estimate: int


def _score_cost(total_cost: float, budget: float) -> float:
    if budget <= 0:
        return 50.0
    ratio = total_cost / budget
    if ratio <= 1:
        return max(0.0, 100.0 - (ratio * 60.0))
    return max(0.0, 40.0 - ((ratio - 1) * 60.0))


def _score_time(minutes: int) -> float:
    return max(0.0, 100.0 - (minutes / 12.0))


def _score_comfort(stops: int, commute_minutes: int) -> float:
    return max(0.0, 100.0 - (stops * 18.0) - (commute_minutes * 0.6))


def choose_plans(
    *,
    flights: list[FlightCandidate],
    stays: list[StayCandidate],
    budget_total: float,
    daily_commute_minutes_estimate: int,
) -> dict[str, OptimizedChoice]:
    flights = flights[:20]
    stays = stays[:20]
    if not flights or not stays:
        raise ValueError("Missing candidates")

    combos: list[tuple[float, float, float, FlightCandidate, StayCandidate]] = []
    for f in flights:
        for s in stays:
            cost = float(f.price_amount) + float(s.total_price_amount)
            time = float(f.duration_minutes)
            comfort = _score_comfort(f.stops, daily_commute_minutes_estimate)
            combos.append((cost, time, comfort, f, s))

    cheapest = min(combos, key=lambda x: x[0])
    fastest = min(combos, key=lambda x: x[1])

    def balanced_key(x: tuple[float, float, float, FlightCandidate, StayCandidate]) -> float:
        cost, time, _comfort, _f, _s = x
        return (1 - (_score_cost(cost, budget_total) / 100.0)) * 0.45 + (1 - (_score_time(int(time)) / 100.0)) * 0.35 + (1 - (_comfort / 100.0)) * 0.20

    balanced = min(combos, key=balanced_key)

    return {
        "cheap": OptimizedChoice(cheapest[3], cheapest[4], daily_commute_minutes_estimate),
        "fast": OptimizedChoice(fastest[3], fastest[4], daily_commute_minutes_estimate),
        "balanced": OptimizedChoice(balanced[3], balanced[4], daily_commute_minutes_estimate),
    }


def compute_scores(*, total_cost: float, budget_total: float, flight_minutes: int, stops: int, commute_minutes: int) -> tuple[float, float, float]:
    return (
        float(_score_cost(total_cost, budget_total)),
        float(_score_time(flight_minutes)),
        float(_score_comfort(stops, commute_minutes)),
    )

