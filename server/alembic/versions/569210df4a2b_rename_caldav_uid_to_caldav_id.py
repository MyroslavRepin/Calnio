"""rename caldav_uid to caldav_id~

Revision ID: 569210df4a2b
Revises: 665c6414c6ba
Create Date: 2025-11-05 17:41:03.275221

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '569210df4a2b'
down_revision: Union[str, Sequence[str], None] = '665c6414c6ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column(
        'notion_tasks',
        'caldav_uid',
        new_column_name='caldav_id'
    )

def downgrade():
    op.alter_column(
        'notion_tasks',
        'caldav_id',
        new_column_name='caldav_uid'
    )
