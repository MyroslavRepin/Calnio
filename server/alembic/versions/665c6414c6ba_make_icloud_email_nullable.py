"""make icloud_email nullable~

Revision ID: 665c6414c6ba
Revises: eca87c3e846a
Create Date: 2025-11-05 17:32:04.010044

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '665c6414c6ba'
down_revision: Union[str, Sequence[str], None] = 'eca87c3e846a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'users',
        'icloud_email',
        existing_type=sa.String(),  # тип колонки
        nullable=True  # разрешаем NULL
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'users',
        'icloud_email',
        existing_type=sa.String(),
        nullable=False  # возвращаем NOT NULL
    )