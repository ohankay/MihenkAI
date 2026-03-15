"""Add generation_kwargs column to model_configs.

Revision ID: 002_add_generation_kwargs
Revises: 001_initial_schema
Create Date: 2026-03-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002_add_generation_kwargs'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'model_configs',
        sa.Column('generation_kwargs', postgresql.JSONB, nullable=True)
    )


def downgrade() -> None:
    op.drop_column('model_configs', 'generation_kwargs')
