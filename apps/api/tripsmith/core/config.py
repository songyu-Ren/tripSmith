from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://tripsmith:tripsmith@postgres:5432/tripsmith"
    redis_url: str = "redis://redis:6379/0"

    llm_provider: str = "mock"
    openrouter_api_key: str | None = None
    openai_api_key: str | None = None

    provider_flights: str = "mock"
    provider_stays: str = "mock"
    provider_poi: str = "opentripmap"
    provider_weather: str = "openmeteo"
    provider_routing: str = "osrm"

    opentripmap_api_key: str | None = None
    kiwi_tequila_api_key: str | None = None

    base_url: str = "http://localhost:3000"
    web_origin: str = "http://localhost:3000"

    rate_limit_per_minute: int = 5
    disable_docs: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

