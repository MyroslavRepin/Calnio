"""Convert datetime columns to timestamptz and add end_date

Revision ID: a3d53bfab21d
Revises: cfef8e5e21e7
Create Date: 2025-09-26 10:36:14.271734

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3d53bfab21d'
down_revision: Union[str, Sequence[str], None] = 'cfef8e5e21e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
