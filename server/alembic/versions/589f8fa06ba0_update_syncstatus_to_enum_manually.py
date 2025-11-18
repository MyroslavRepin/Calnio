"""Update syncstatus to enum manually

Revision ID: 589f8fa06ba0
Revises: 086698cdd088
Create Date: 2025-10-30 23:44:42.568042

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '589f8fa06ba0'
down_revision: Union[str, Sequence[str], None] = '086698cdd088'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade sync_status enum from ('pending','done','failed') to ('pending','success','failed')."""

    # 1️⃣ Drop defaults first
    op.execute("ALTER TABLE notion_tasks ALTER COLUMN sync_status DROP DEFAULT;")
    op.execute("ALTER TABLE caldav_events ALTER COLUMN sync_status DROP DEFAULT;")

    # 2️⃣ Rename old enum
    op.execute("ALTER TYPE syncstatus RENAME TO syncstatus_old;")

    # 3️⃣ Create new enum
    op.execute("CREATE TYPE syncstatus AS ENUM ('pending', 'success', 'failed');")

    # 4️⃣ Update columns to new enum
    op.execute("""
        ALTER TABLE notion_tasks
        ALTER COLUMN sync_status TYPE syncstatus
        USING CASE
            WHEN sync_status::text = 'done' THEN 'success'::syncstatus
            WHEN sync_status::text = 'pending' THEN 'pending'::syncstatus
            WHEN sync_status::text = 'failed' THEN 'failed'::syncstatus
            ELSE 'pending'::syncstatus
        END;
    """)
    op.execute("""
        ALTER TABLE caldav_events
        ALTER COLUMN sync_status TYPE syncstatus
        USING CASE
            WHEN sync_status::text = 'done' THEN 'success'::syncstatus
            WHEN sync_status::text = 'pending' THEN 'pending'::syncstatus
            WHEN sync_status::text = 'failed' THEN 'failed'::syncstatus
            ELSE 'pending'::syncstatus
        END;
    """)

    # 5️⃣ Drop old enum
    op.execute("DROP TYPE syncstatus_old;")

    # 6️⃣ Set defaults
    op.alter_column('notion_tasks', 'sync_status', server_default=sa.text("'pending'::syncstatus"))
    op.alter_column('caldav_events', 'sync_status', server_default=sa.text("'pending'::syncstatus"))


def downgrade() -> None:
    """Downgrade sync_status enum from ('pending','success','failed') to ('pending','done','failed')."""

    # 1️⃣ Drop defaults first
    op.execute("ALTER TABLE notion_tasks ALTER COLUMN sync_status DROP DEFAULT;")
    op.execute("ALTER TABLE caldav_events ALTER COLUMN sync_status DROP DEFAULT;")

    # 2️⃣ Rename current enum
    op.execute("ALTER TYPE syncstatus RENAME TO syncstatus_new;")

    # 3️⃣ Create old enum
    op.execute("CREATE TYPE syncstatus AS ENUM ('pending', 'done', 'failed');")

    # 4️⃣ Update columns to old enum
    op.execute("""
        ALTER TABLE notion_tasks
        ALTER COLUMN sync_status TYPE syncstatus
        USING CASE
            WHEN sync_status::text = 'success' THEN 'done'::syncstatus
            WHEN sync_status::text = 'pending' THEN 'pending'::syncstatus
            WHEN sync_status::text = 'failed' THEN 'failed'::syncstatus
            ELSE 'pending'::syncstatus
        END;
    """)
    op.execute("""
        ALTER TABLE caldav_events
        ALTER COLUMN sync_status TYPE syncstatus
        USING CASE
            WHEN sync_status::text = 'success' THEN 'done'::syncstatus
            WHEN sync_status::text = 'pending' THEN 'pending'::syncstatus
            WHEN sync_status::text = 'failed' THEN 'failed'::syncstatus
            ELSE 'pending'::syncstatus
        END;
    """)

    # 5️⃣ Drop new enum
    op.execute("DROP TYPE syncstatus_new;")

    # 6️⃣ Set defaults
    op.alter_column('notion_tasks', 'sync_status', server_default=sa.text("'pending'::syncstatus"))
    op.alter_column('caldav_events', 'sync_status', server_default=sa.text("'pending'::syncstatus"))