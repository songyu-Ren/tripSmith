from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from tripsmith.models.base import Base


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    trip_id: Mapped[str] = mapped_column(String(36), index=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), index=True)

    phase: Mapped[str] = mapped_column(String(32), index=True)
    input_json: Mapped[dict] = mapped_column(JSON)
    output_json: Mapped[dict] = mapped_column(JSON)
    tool_calls_json: Mapped[list] = mapped_column(JSON)
    model_info: Mapped[dict] = mapped_column(JSON)
    prompt_version: Mapped[str] = mapped_column(String(64))
    commit_hash: Mapped[str] = mapped_column(String(64))

