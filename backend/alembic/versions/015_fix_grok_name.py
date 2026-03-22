"""Fix Grok default display name for llama-3.1-8b-instant.

Revision ID: 015_fix_grok_name
Revises: 014_set_grok_llama31
Create Date: 2026-03-22 00:00:05.000000
"""
from alembic import op
from sqlalchemy import text


revision = "015_fix_grok_name"
down_revision = "014_set_grok_llama31"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text(
            """
            UPDATE model_configs
            SET name = 'Llama 3.1 8B Instant Grok Default'
            WHERE provider = 'Grok'
              AND model_name = 'llama-3.1-8b-instant'
              AND name IN ('Llama3 8B Grok Default', 'Grok 2 Default', 'Llama 3.3 Grok Default')
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text(
            """
            UPDATE model_configs
            SET name = 'Llama3 8B Grok Default'
            WHERE provider = 'Grok'
              AND model_name = 'llama-3.1-8b-instant'
              AND name = 'Llama 3.1 8B Instant Grok Default'
            """
        )
    )
