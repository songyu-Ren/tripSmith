from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import fakeredis

from tripsmith.main import create_app
from tripsmith.main import redis_dep
from tripsmith.core.db import get_db
from tripsmith.models.base import Base
from tripsmith.models.alert import Alert
from tripsmith.models.itinerary import Itinerary
from tripsmith.models.notification import Notification
from tripsmith.models.plan import Plan
from tripsmith.models.trip import Trip


_MODEL_IMPORTS = (Trip, Plan, Itinerary, Alert, Notification)


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    app = create_app()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    r = fakeredis.FakeRedis(decode_responses=True)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[redis_dep] = lambda: r

    return TestClient(app)

