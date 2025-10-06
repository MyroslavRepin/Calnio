"""Add active_sync column manually

Revision ID: f74ea4b9e097
Revises: 424907f7e342
Create Date: 2025-10-02 10:37:38.562127

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f74ea4b9e097'
down_revision: Union[str, Sequence[str], None] = '424907f7e342'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the new column to the correct table
    op.add_column('users', sa.Column('active_sync', sa.Boolean(), nullable=False, server_default=sa.false()))
    # Explicitly set active_sync=False for all existing users
    op.execute("UPDATE users SET active_sync = FALSE")
    # Remove server_default to avoid future inserts defaulting to False (optional)
    op.alter_column('users', 'active_sync', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    pass
