"""add system_prompt to model_configs

Revision ID: 009_add_system_prompt
Revises: 008_add_llm_query_logs
Create Date: 2026-03-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "009_add_system_prompt"
down_revision = "008_add_llm_query_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "model_configs",
        sa.Column("system_prompt", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("model_configs", "system_prompt")
