"""Remove Ollama defaults and set Grok llama-3.1-8b-instant as seeded default.

Revision ID: 010_rm_ollama_set_grok_llama33
Revises: 009_add_system_prompt
Create Date: 2026-03-22 00:00:00.000000
"""
from alembic import op
from sqlalchemy import text

revision = "010_rm_ollama_set_grok_llama33"
down_revision = "009_add_system_prompt"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Remove previously seeded/default Ollama entries.
    conn.execute(
        text("DELETE FROM model_configs WHERE provider = 'Ollama'")
    )

    # Normalize Grok default to llama-3.1-8b-instant for rows that are still unconfigured.
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
            WHERE provider = 'Grok' AND api_key IS NULL
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()

    # Keep provider strategy consistent: do not reintroduce deprecated providers.
    # Roll back only the Grok seeded naming/model defaults for unconfigured rows.
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
            WHERE provider = 'Grok' AND api_key IS NULL
            """
        )
    )


