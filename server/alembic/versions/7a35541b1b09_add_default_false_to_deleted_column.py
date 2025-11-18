"""Add default false to deleted column

Revision ID: 7a35541b1b09
Revises: 23502f720669
Create Date: 2025-11-05 20:15:32.396046

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Boolean, text


# revision identifiers, used by Alembic.
revision: str = '7a35541b1b09'
down_revision: Union[str, Sequence[str], None] = '23502f720669'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    from alembic import op
    op.alter_column(
        'notion_tasks',
        'deleted',
        existing_type=Boolean(),
        server_default=text('false'),
        nullable=False
    )

def downgrade() -> None:
    from alembic import op
    op.alter_column(
        'notion_tasks',
        'deleted',
        existing_type=Boolean(),
        server_default=None,
        nullable=True
    )