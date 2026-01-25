from __future__ import annotations

from tripsmith.core.config import settings
from tripsmith.providers.base import FlightsProvider
from tripsmith.providers.base import PoiProvider
from tripsmith.providers.base import RoutingProvider
from tripsmith.providers.base import StaysProvider
from tripsmith.providers.base import WeatherProvider
from tripsmith.providers.flights_amadeus_stub import AmadeusFlightsProvider
from tripsmith.providers.flights_duffel_stub import DuffelFlightsProvider
from tripsmith.providers.flights_kiwi import KiwiTequilaFlightsProvider
from tripsmith.providers.mock_provider import MockFlightsProvider
from tripsmith.providers.mock_provider import MockPoiProvider
from tripsmith.providers.mock_provider import MockRoutingProvider
from tripsmith.providers.mock_provider import MockStaysProvider
from tripsmith.providers.mock_provider import MockWeatherProvider
from tripsmith.providers.openmeteo import OpenMeteoWeatherProvider
from tripsmith.providers.opentripmap import OpenTripMapPoiProvider
from tripsmith.providers.osrm import OsrmRoutingProvider
from tripsmith.providers.stays_booking_stub import BookingStaysProvider


def get_flights_provider() -> FlightsProvider:
    if settings.provider_flights == "amadeus":
        return AmadeusFlightsProvider()
    if settings.provider_flights == "duffel":
        return DuffelFlightsProvider()
    if settings.provider_flights == "kiwi" and settings.kiwi_tequila_api_key:
        return KiwiTequilaFlightsProvider(api_key=settings.kiwi_tequila_api_key)
    return MockFlightsProvider()


def get_stays_provider() -> StaysProvider:
    if settings.provider_stays == "booking_stub":
        return BookingStaysProvider()
    return MockStaysProvider()


def get_poi_provider() -> PoiProvider:
    if settings.provider_poi == "opentripmap" and settings.opentripmap_api_key:
        return OpenTripMapPoiProvider(api_key=settings.opentripmap_api_key)
    return MockPoiProvider()


def get_weather_provider() -> WeatherProvider:
    if settings.provider_weather == "openmeteo":
        return OpenMeteoWeatherProvider()
    return MockWeatherProvider()


def get_routing_provider() -> RoutingProvider:
    if settings.provider_routing == "osrm":
        return OsrmRoutingProvider()
    return MockRoutingProvider()

