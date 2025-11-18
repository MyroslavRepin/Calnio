"""add deletede to UserNotoinTasks and CalDavEvents

Revision ID: eca87c3e846a
Revises: 589f8fa06ba0
Create Date: 2025-10-31 23:21:01.901163

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eca87c3e846a'
down_revision: Union[str, Sequence[str], None] = '589f8fa06ba0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("notion_tasks", sa.Column("deleted", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("caldav_events", sa.Column("deleted", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("notion_tasks", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("caldav_events", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

def downgrade() -> None:
    op.drop_column("notion_tasks", "deleted")
    op.drop_column("caldav_events", "deleted")
    op.drop_column("notion_tasks", "deleted_at")
    op.drop_column("caldav_events", "deleted_at")