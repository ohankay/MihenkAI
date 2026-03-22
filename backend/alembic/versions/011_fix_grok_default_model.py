"""Fix Grok seeded default model to llama-3.1-8b-instant on Groq endpoint.

Revision ID: 011_fix_grok_default_model
Revises: 010_rm_ollama_set_grok_llama33
Create Date: 2026-03-22 00:00:01.000000
"""
from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "011_fix_grok_default_model"
down_revision = "010_rm_ollama_set_grok_llama33"
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
                    WHEN name IS NULL OR name IN ('Llama 3.3 Grok Default', 'Grok 2 Default') THEN 'Llama 3.1 8B Instant Grok Default'
                    ELSE name
                END
            WHERE provider = 'Grok'
              AND model_name IN ('llama-3.3-70b', 'grok-2-latest')
              AND (api_key IS NULL OR api_key = '')
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
              AND (api_key IS NULL OR api_key = '')
            """
        )
    )


