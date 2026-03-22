"""Set Grok default model to llama-3.1-8b-instant.

Revision ID: 014_set_grok_llama31
Revises: 013_set_grok_llama3_8b
Create Date: 2026-03-22 00:00:04.000000
"""
from alembic import op
from sqlalchemy import text


revision = "014_set_grok_llama31"
down_revision = "013_set_grok_llama3_8b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text(
            """
            UPDATE model_configs
            SET model_name = 'llama-3.1-8b-instant',
                base_url = 'https://api.groq.com/openai/v1',
                name = CASE
                    WHEN name IS NULL OR name IN (
                        'Llama 3.3 Grok Default',
                        'Grok 2 Default',
                        'Llama3 8B Grok Default',
                        'Llama 3.1 8B Instant Grok Default'
                    ) THEN 'Llama 3.1 8B Instant Grok Default'
                    ELSE name
                END
            WHERE provider = 'Grok'
              AND model_name IN ('llama-3.3-70b', 'grok-2-latest', 'llama3-8b-8192')
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text(
            """
            UPDATE model_configs
            SET model_name = 'llama3-8b-8192',
                base_url = 'https://api.groq.com/openai/v1',
                name = CASE
                    WHEN name = 'Llama 3.1 8B Instant Grok Default' THEN 'Llama3 8B Grok Default'
                    ELSE name
                END
            WHERE provider = 'Grok'
              AND model_name = 'llama-3.1-8b-instant'
            """
        )
    )
