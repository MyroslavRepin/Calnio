"""add end_date to notion_tasks

Revision ID: cfef8e5e21e7
Revises: 195306bb06b8
Create Date: 2025-09-26 10:16:07.613893

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cfef8e5e21e7'
down_revision: Union[str, Sequence[str], None] = '195306bb06b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('notion_tasks', sa.Column('end_date', sa.TIMESTAMP(timezone=True), nullable=True))

    # optional: проставить end_date = start_date для существующих записей
    op.execute("""
        UPDATE notion_tasks
        SET end_date = start_date
        WHERE end_date IS NULL
    """)

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('notion_tasks', 'end_date')
