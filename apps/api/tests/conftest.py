from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

import fakeredis

from tripsmith.main import create_app
from tripsmith.main import redis_dep
from tripsmith.core import db as db_core
from tripsmith.core.db import get_db
from tripsmith.models.base import Base
from tripsmith.models.alert import Alert
from tripsmith.models.itinerary import Itinerary
from tripsmith.models.notification import Notification
from tripsmith.models.plan import Plan
from tripsmith.models.trip import Trip
from tripsmith.models.agent_run import AgentRun
from tripsmith.models.job import Job
from tripsmith.models.saved_plan import SavedPlan


_MODEL_IMPORTS = (Trip, Plan, Itinerary, Alert, Notification, AgentRun, Job, SavedPlan)


@pytest.fixture()
def client():
    os.environ["CELERY_ALWAYS_EAGER"] = "1"
    os.environ["FAKE_REDIS"] = "1"
    db_core.reconfigure_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=db_core.engine)

    app = create_app()

    def override_get_db():
        db = db_core.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    r = fakeredis.FakeRedis(decode_responses=True)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[redis_dep] = lambda: r

    return TestClient(app)

