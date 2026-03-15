"""Seed default Judge LLM configurations for common providers.

Revision ID: 003_seed_judge_llm_configs
Revises: 002_add_generation_kwargs
Create Date: 2026-03-15 00:00:00.000000

Inserts one pre-configured entry per major LLM provider so users can get started
quickly by just adding their API key.  All entries use temperature=0 and
max_tokens=2000 which are the recommended defaults for DeepEval judge models.

base_url is pre-filled for providers that require a non-default endpoint
(Gemini, Grok, DeepSeek, Ollama). api_key is intentionally left NULL —
users must fill in their own credentials.
"""
from alembic import op

revision = '003_seed_judge_llm_configs'
down_revision = '002_add_generation_kwargs'
branch_labels = None
depends_on = None

# fmt: off
_SEEDS = [
    # (provider, model_name, base_url)
    # api_key left NULL — user fills in their own
    ("OpenAI",    "gpt-4o",                          None),
    ("Anthropic", "claude-3-5-sonnet-20241022",       None),
    ("Gemini",    "gemini-1.5-pro",                   "https://generativelanguage.googleapis.com/v1beta/openai/"),
    ("Grok",      "grok-2-latest",                    "https://api.x.ai/v1"),
    ("DeepSeek",  "deepseek-chat",                    "https://api.deepseek.com/v1"),
    ("Ollama",    "llama3.1",                         "http://host.docker.internal:11434/v1"),
]
# fmt: on

_GENERATION_KWARGS = '{"max_tokens": 2000}'


def upgrade() -> None:
    conn = op.get_bind()
    for provider, model_name, base_url in _SEEDS:
        # Skip if an entry for this provider already exists (idempotent)
        existing = conn.execute(
            __import__("sqlalchemy").text(
                "SELECT 1 FROM model_configs WHERE provider = :p LIMIT 1"
            ),
            {"p": provider},
        ).fetchone()
        if existing:
            continue

        if base_url:
            conn.execute(
                __import__("sqlalchemy").text(
                    """
                    INSERT INTO model_configs
                        (provider, model_name, api_key, base_url, temperature, generation_kwargs, created_at, updated_at)
                    VALUES
                        (:provider, :model_name, NULL, :base_url, 0.0,
                         CAST(:gen_kwargs AS jsonb), NOW(), NOW())
                    """
                ),
                {
                    "provider": provider,
                    "model_name": model_name,
                    "base_url": base_url,
                    "gen_kwargs": _GENERATION_KWARGS,
                },
            )
        else:
            conn.execute(
                __import__("sqlalchemy").text(
                    """
                    INSERT INTO model_configs
                        (provider, model_name, api_key, base_url, temperature, generation_kwargs, created_at, updated_at)
                    VALUES
                        (:provider, :model_name, NULL, NULL, 0.0,
                         CAST(:gen_kwargs AS jsonb), NOW(), NOW())
                    """
                ),
                {
                    "provider": provider,
                    "model_name": model_name,
                    "gen_kwargs": _GENERATION_KWARGS,
                },
            )


def downgrade() -> None:
    conn = op.get_bind()
    providers = [p for p, _, _ in _SEEDS]
    conn.execute(
        __import__("sqlalchemy").text(
            "DELETE FROM model_configs WHERE provider = ANY(:providers) AND api_key IS NULL"
        ),
        {"providers": providers},
    )
