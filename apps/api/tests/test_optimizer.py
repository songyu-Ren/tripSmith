from __future__ import annotations

from tripsmith.agent.optimizer import choose_plans
from tripsmith.providers.base import FlightCandidate
from tripsmith.providers.base import GeoPoint
from tripsmith.providers.base import StayCandidate


def test_optimizer_picks_within_budget_when_possible():
    flights = [
        FlightCandidate(
            id="f1",
            depart_at="2030-01-01T10:00:00",
            arrive_at="2030-01-01T18:00:00",
            stops=0,
            duration_minutes=480,
            price_amount=200,
            currency="USD",
        ),
        FlightCandidate(
            id="f2",
            depart_at="2030-01-01T12:00:00",
            arrive_at="2030-01-01T22:00:00",
            stops=1,
            duration_minutes=600,
            price_amount=600,
            currency="USD",
        ),
    ]
    stays = [
        StayCandidate(
            id="s1",
            name="Stay",
            area="Center",
            location=GeoPoint(lat=0.0, lon=0.0),
            nightly_price_amount=100,
            total_price_amount=500,
            currency="USD",
        ),
        StayCandidate(
            id="s2",
            name="Stay",
            area="Center",
            location=GeoPoint(lat=0.0, lon=0.0),
            nightly_price_amount=200,
            total_price_amount=900,
            currency="USD",
        ),
    ]
    out = choose_plans(flights=flights, stays=stays, budget_total=800, daily_commute_minutes_estimate=20)
    cheap = out["cheap"]
    assert float(cheap.flight.price_amount) + float(cheap.stay.total_price_amount) <= 800

