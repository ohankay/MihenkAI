"""add llm query logs table

Revision ID: 008_add_llm_query_logs
Revises: 007_add_job_payloads
Create Date: 2026-03-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "008_add_llm_query_logs"
down_revision = "007_add_job_payloads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "llm_query_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("model_config_id", sa.Integer(), sa.ForeignKey("model_configs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("response", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_llm_query_logs_model_config_id", "llm_query_logs", ["model_config_id"])
    op.create_index("ix_llm_query_logs_created_at", "llm_query_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_llm_query_logs_created_at", table_name="llm_query_logs")
    op.drop_index("ix_llm_query_logs_model_config_id", table_name="llm_query_logs")
    op.drop_table("llm_query_logs")
