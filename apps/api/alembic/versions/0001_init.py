"""init

Revision ID: 0001_init
Revises:
Create Date: 2026-01-25

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trips",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("origin", sa.String(length=128), nullable=False),
        sa.Column("destination", sa.String(length=128), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("flexible_days", sa.Integer, nullable=False, server_default="0"),
        sa.Column("budget_total", sa.Numeric, nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="USD"),
        sa.Column("travelers", sa.Integer, nullable=False, server_default="1"),
        sa.Column("preferences", sa.JSON, nullable=False, server_default=sa.text("'{}'")),
    )

    op.create_table(
        "plans",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("trip_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("plans_json", sa.JSON, nullable=False),
        sa.Column("explain_md", sa.Text, nullable=False),
    )

    op.create_table(
        "itineraries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("trip_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("plan_index", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("itinerary_json", sa.JSON, nullable=False),
        sa.Column("itinerary_md", sa.Text, nullable=False),
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("trip_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("threshold", sa.Numeric, nullable=False),
        sa.Column("frequency_minutes", sa.Integer, nullable=False),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("alert_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("channel", sa.String(length=16), nullable=False, server_default="email"),
        sa.Column("payload_json", sa.JSON, nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="queued"),
    )


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("alerts")
    op.drop_table("itineraries")
    op.drop_table("plans")
    op.drop_table("trips")

