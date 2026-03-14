"""Initial schema setup.

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-03-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables for MihenkAI."""
    
    # Create model_configs table
    op.create_table(
        'model_configs',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('provider', sa.String(50), nullable=False),  # OpenAI, Anthropic, Ollama, vLLM
        sa.Column('model_name', sa.String(255), nullable=False),  # gpt-4o, llama3, etc.
        sa.Column('api_key', sa.Text, nullable=True),  # Encrypted
        sa.Column('base_url', sa.String(255), nullable=True),  # For local models
        sa.Column('temperature', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create evaluation_profiles table
    op.create_table(
        'evaluation_profiles',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('model_config_id', sa.Integer, sa.ForeignKey('model_configs.id'), nullable=False),
        sa.Column('single_weights', postgresql.JSONB, nullable=False, server_default='{}'),  # {"faithfulness": 0.6, "answer_relevancy": 0.4}
        sa.Column('conversational_weights', postgresql.JSONB, nullable=False, server_default='{}'),  # {"knowledge_retention": 0.5, ...}
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Create evaluation_jobs table
    op.create_table(
        'evaluation_jobs',
        sa.Column('job_id', sa.String(50), primary_key=True),  # eval-{uuid4}
        sa.Column('profile_id', sa.Integer, sa.ForeignKey('evaluation_profiles.id'), nullable=False),
        sa.Column('evaluation_type', sa.String(50), nullable=False),  # SINGLE, CONVERSATIONAL
        sa.Column('status', sa.String(50), nullable=False, server_default='QUEUED'),  # QUEUED, PROCESSING, COMPLETED, FAILED
        sa.Column('composite_score', sa.Float, nullable=True),  # 0-100
        sa.Column('metrics_breakdown', postgresql.JSONB, nullable=True),  # {metric: {score, weight}}
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True),
    )
    
    # Create indexes for performance
    op.create_index('ix_model_configs_provider', 'model_configs', ['provider'])
    op.create_index('ix_evaluation_profiles_model_config_id', 'evaluation_profiles', ['model_config_id'])
    op.create_index('ix_evaluation_jobs_profile_id', 'evaluation_jobs', ['profile_id'])
    op.create_index('ix_evaluation_jobs_status', 'evaluation_jobs', ['status'])
    op.create_index('ix_evaluation_jobs_created_at', 'evaluation_jobs', ['created_at'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('evaluation_jobs')
    op.drop_table('evaluation_profiles')
    op.drop_table('model_configs')
