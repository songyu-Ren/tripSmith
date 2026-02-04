from __future__ import annotations

import datetime as dt

from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from tripsmith.models.base import Base


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))

    origin: Mapped[str] = mapped_column(String(128))
    destination: Mapped[str] = mapped_column(String(128))
    start_date: Mapped[dt.date] = mapped_column(Date)
    end_date: Mapped[dt.date] = mapped_column(Date)
    flexible_days: Mapped[int] = mapped_column(Integer)

    budget_total: Mapped[float] = mapped_column(Numeric)
    currency: Mapped[str] = mapped_column(String(8))
    travelers: Mapped[int] = mapped_column(Integer)
    preferences: Mapped[dict] = mapped_column(JSON)

    constraints_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    constraints_confirmed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

