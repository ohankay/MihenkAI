"""Add name column to model_configs and backfill seeded rows.

Revision ID: 004_add_name_to_model_configs
Revises: 003_seed_judge_llm_configs
Create Date: 2026-03-15 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '004_add_name_to_model_configs'
down_revision = '003_seed_judge_llm_configs'
branch_labels = None
depends_on = None

# Default names for the seed rows inserted by migration 003. Matched by
# provider so the backfill is safe even if rows were added or deleted manually.
_BACKFILL = {
    "OpenAI":    "GPT-4o Default",
    "Anthropic": "Claude 3.5 Sonnet Default",
    "Gemini":    "Gemini 1.5 Pro Default",
    "Grok":      "Llama 3.1 8B Instant Grok Default",
    "DeepSeek":  "DeepSeek Chat Default",
}


def upgrade() -> None:
    # Add nullable name column
    op.add_column(
        'model_configs',
        sa.Column('name', sa.String(255), nullable=True)
    )

    conn = op.get_bind()
    text = __import__("sqlalchemy").text

    # Backfill seed rows that have no name yet
    for provider, default_name in _BACKFILL.items():
        conn.execute(
            text(
                "UPDATE model_configs SET name = :name "
                "WHERE provider = :provider AND name IS NULL"
            ),
            {"name": default_name, "provider": provider},
        )


def downgrade() -> None:
    op.drop_column('model_configs', 'name')
