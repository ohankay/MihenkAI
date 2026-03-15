"""Remove model_config_id from evaluation_profiles.

Revision ID: 005_drop_profile_judge_llm
Revises: 004_add_name_to_model_configs
Create Date: 2026-03-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '005_drop_profile_judge_llm'
down_revision = '004_add_name_to_model_configs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index('ix_evaluation_profiles_model_config_id', table_name='evaluation_profiles')
    op.drop_constraint(
        'evaluation_profiles_model_config_id_fkey',
        'evaluation_profiles',
        type_='foreignkey'
    )
    op.drop_column('evaluation_profiles', 'model_config_id')


def downgrade() -> None:
    op.add_column('evaluation_profiles',
        sa.Column('model_config_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'evaluation_profiles_model_config_id_fkey',
        'evaluation_profiles', 'model_configs',
        ['model_config_id'], ['id']
    )
    op.create_index('ix_evaluation_profiles_model_config_id', 'evaluation_profiles', ['model_config_id'])
