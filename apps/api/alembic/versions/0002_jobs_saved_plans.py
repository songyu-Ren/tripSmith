"""jobs and saved plans

Revision ID: 0002_jobs_saved_plans
Revises: 0001_init
Create Date: 2026-01-26

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_jobs_saved_plans"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("trip_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("user_id", sa.String(length=64), nullable=False, index=True),
        sa.Column("type", sa.String(length=16), nullable=False, index=True),
        sa.Column("status", sa.String(length=16), nullable=False, index=True),
        sa.Column("progress", sa.Integer, nullable=False),
        sa.Column("message", sa.String(length=256), nullable=False),
        sa.Column("result_json", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, index=True),
    )

    op.create_table(
        "saved_plans",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("trip_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("plan_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("plan_index", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("label", sa.String(length=64), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("saved_plans")
    op.drop_table("jobs")

