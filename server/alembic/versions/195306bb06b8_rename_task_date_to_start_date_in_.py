"""rename task_date to start_date in notion_tasks

Revision ID: 195306bb06b8
Revises: 723eede5975e
Create Date: 2025-09-26 10:05:46.285797

"""
"""rename task_date to start_date in notion_tasks

Revision ID: 195306bb06b8
Revises: 723eede5975e
Create Date: 2025-09-26 10:05:46.285797

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '195306bb06b8'
down_revision: Union[str, Sequence[str], None] = '723eede5975e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.alter_column('notion_tasks', 'task_date', new_column_name='start_date')

def downgrade():
    op.alter_column('notion_tasks', 'start_date', new_column_name='task_date')
