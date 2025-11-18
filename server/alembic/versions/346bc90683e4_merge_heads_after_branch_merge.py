"""Merge heads after branch merge

Revision ID: 346bc90683e4
Revises: a4ab66b804c6, f0995c8c6da0
Create Date: 2025-10-30 23:19:25.200763

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '346bc90683e4'
down_revision: Union[str, Sequence[str], None] = ('a4ab66b804c6', 'f0995c8c6da0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
