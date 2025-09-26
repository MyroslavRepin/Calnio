"""Add sync_interval to users table

Revision ID: b9f5a4a9d0d8
Revises: 
Create Date: 2025-09-26 16:57:53.113977

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9f5a4a9d0d8'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add sync_interval column to users table with default value of 30 minutes
    op.add_column('users', sa.Column('sync_interval', sa.Integer(), nullable=False, server_default='30'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove sync_interval column from users table
    op.drop_column('users', 'sync_interval')
