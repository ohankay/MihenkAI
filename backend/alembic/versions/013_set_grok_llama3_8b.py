"""Set Grok default model to llama-3.1-8b-instant on Groq endpoint.

Revision ID: 013_set_grok_llama3_8b
Revises: 012_fix_grok_invalid_model
Create Date: 2026-03-22 00:00:03.000000
"""
from alembic import op
from sqlalchemy import text


revision = "013_set_grok_llama3_8b"
down_revision = "012_fix_grok_invalid_model"
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
                    WHEN name IS NULL OR name IN ('Llama 3.3 Grok Default', 'Grok 2 Default')
                        THEN 'Llama 3.1 8B Instant Grok Default'
                    ELSE name
                END
            WHERE provider = 'Grok'
              AND model_name IN ('llama-3.3-70b', 'grok-2-latest')
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        text(
            """
            UPDATE model_configs
            SET model_name = 'grok-2-latest',
                base_url = 'https://api.x.ai/v1',
                name = CASE
                    WHEN name = 'Llama 3.1 8B Instant Grok Default' THEN 'Grok 2 Default'
                    ELSE name
                END
            WHERE provider = 'Grok'
              AND model_name = 'llama-3.1-8b-instant'
            """
        )
    )


