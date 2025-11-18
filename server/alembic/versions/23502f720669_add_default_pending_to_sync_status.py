"""add default pending to sync_status

Revision ID: 23502f720669
Revises: 569210df4a2b
Create Date: 2025-11-05 20:12:28.483717

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23502f720669'
down_revision: Union[str, Sequence[str], None] = '569210df4a2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'notion_tasks',
        'sync_status',
        existing_type=sa.String(),  # если VARCHAR
        server_default='pending',
        existing_nullable=False
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'notion_tasks',
        'sync_status',
        existing_type=sa.String(),
        server_default=None,
        existing_nullable=False
    )
