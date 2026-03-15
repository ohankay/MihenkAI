"""Add single_negative_thresholds to evaluation_profiles.

Revision ID: 006_add_negative_thresholds
Revises: 005_drop_profile_judge_llm
Create Date: 2026-03-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '006_add_negative_thresholds'
down_revision = '005_drop_profile_judge_llm'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'evaluation_profiles',
        sa.Column(
            'single_negative_thresholds',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default='{}',
        ),
    )


def downgrade() -> None:
    op.drop_column('evaluation_profiles', 'single_negative_thresholds')
