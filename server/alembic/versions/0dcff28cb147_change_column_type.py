"""change column type

Revision ID: 0dcff28cb147
Revises: 040918af799d
Create Date: 2025-10-24 11:33:47.460423

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0dcff28cb147'
down_revision: Union[str, Sequence[str], None] = '040918af799d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    sync_status_enum = postgresql.ENUM('pending', 'done', 'failed', name='syncstatus', create_type=True)
    sync_status_enum.create(op.get_bind(), checkfirst=True)

    # Убираем старый default перед изменением типа
    op.alter_column('notion_tasks', 'sync_status', server_default=None)
    op.alter_column('caldav_events', 'sync_status', server_default=None)

    # Меняем тип колонок на ENUM
    op.alter_column('notion_tasks', 'sync_status',
                    type_=sync_status_enum,
                    postgresql_using="sync_status::syncstatus")
    op.alter_column('caldav_events', 'sync_status',
                    type_=sync_status_enum,
                    postgresql_using="sync_status::syncstatus")

    # Назначаем новый default уже для ENUM
    op.alter_column('notion_tasks', 'sync_status', server_default='pending')
    op.alter_column('caldav_events', 'sync_status', server_default='pending')

def downgrade() -> None:
    op.drop_column('caldav_events', 'sync_status')
    op.drop_column('notion_tasks', 'sync_status')
    op.alter_column('notion_tasks', 'caldav_id', new_column_name='caldav_id')

    # удалить тип ENUM
    sync_status_enum = postgresql.ENUM('pending', 'done', 'failed', name='syncstatus')
    sync_status_enum.drop(op.get_bind(), checkfirst=True)
