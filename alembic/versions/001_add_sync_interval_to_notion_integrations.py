"""Add sync_interval to notion_integrations

Revision ID: 001
Revises: 
Create Date: 2024-09-26 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add sync_interval column to notion_integrations table
    op.add_column('notion_integrations', sa.Column('sync_interval', sa.Integer(), nullable=False, server_default='30'))


def downgrade() -> None:
    # Remove sync_interval column from notion_integrations table
    op.drop_column('notion_integrations', 'sync_interval')