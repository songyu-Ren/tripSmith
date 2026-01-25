from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from tripsmith.models.base import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    trip_id: Mapped[str] = mapped_column(String(36), index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))

    plans_json: Mapped[dict] = mapped_column(JSON)
    explain_md: Mapped[str] = mapped_column(Text)

