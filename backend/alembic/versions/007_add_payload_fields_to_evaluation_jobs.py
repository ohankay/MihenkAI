"""add payload fields to evaluation jobs

Revision ID: 007_add_job_payloads
Revises: 006_add_negative_thresholds
Create Date: 2026-03-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "007_add_job_payloads"
down_revision = "006_add_negative_thresholds"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "evaluation_jobs",
        sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "evaluation_jobs",
        sa.Column("result_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("evaluation_jobs", "result_payload")
    op.drop_column("evaluation_jobs", "request_payload")
