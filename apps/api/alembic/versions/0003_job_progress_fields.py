"""job progress fields

Revision ID: 0003_job_progress_fields
Revises: 0002_jobs_saved_plans
Create Date: 2026-02-06

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_job_progress_fields"
down_revision = "0002_jobs_saved_plans"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("stage", sa.String(length=32), nullable=False, server_default="QUEUED"),
    )
    op.add_column("jobs", sa.Column("error_code", sa.String(length=64), nullable=True))
    op.add_column("jobs", sa.Column("error_message", sa.String(length=256), nullable=True))
    op.add_column("jobs", sa.Column("next_action", sa.String(length=256), nullable=True))
    op.alter_column("jobs", "stage", server_default=None)


def downgrade() -> None:
    op.drop_column("jobs", "next_action")
    op.drop_column("jobs", "error_message")
    op.drop_column("jobs", "error_code")
    op.drop_column("jobs", "stage")
