"""update_syncstatus_enum_values

Revision ID: f0995c8c6da0
Revises: 19fc4fe2811f
Create Date: 2025-10-31 00:34:33.891762

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f0995c8c6da0'
down_revision: Union[str, Sequence[str], None] = '19fc4fe2811f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - update syncstatus enum from ('pending','done','failed') to ('pending','success','failed')."""
    
    # Step 1: Rename old enum type
    op.execute("ALTER TYPE syncstatus RENAME TO syncstatus_old")
    
    # Step 2: Create new enum type with correct values
    op.execute("CREATE TYPE syncstatus AS ENUM ('pending', 'success', 'failed')")
    
    # Step 3: Update notion_tasks.sync_status column to use new type
    # Map 'done' -> 'success' during migration
    op.execute("""
        ALTER TABLE notion_tasks 
        ALTER COLUMN sync_status TYPE syncstatus 
        USING CASE 
            WHEN sync_status::text = 'done' THEN 'success'::syncstatus
            ELSE sync_status::text::syncstatus
        END
    """)
    
    # Step 4: Update caldav_events.sync_status column to use new type
    # Map 'done' -> 'success' during migration
    op.execute("""
        ALTER TABLE caldav_events 
        ALTER COLUMN sync_status TYPE syncstatus 
        USING CASE 
            WHEN sync_status::text = 'done' THEN 'success'::syncstatus
            ELSE sync_status::text::syncstatus
        END
    """)
    
    # Step 5: Drop old enum type
    op.execute("DROP TYPE syncstatus_old")
    
    # Step 6: Set default values using the new enum
    op.alter_column('notion_tasks', 'sync_status', server_default=sa.text("'pending'::syncstatus"))
    op.alter_column('caldav_events', 'sync_status', server_default=sa.text("'pending'::syncstatus"))


def downgrade() -> None:
    """Downgrade schema - revert syncstatus enum from ('pending','success','failed') to ('pending','done','failed')."""
    
    # Step 1: Rename current enum type
    op.execute("ALTER TYPE syncstatus RENAME TO syncstatus_new")
    
    # Step 2: Create old enum type
    op.execute("CREATE TYPE syncstatus AS ENUM ('pending', 'done', 'failed')")
    
    # Step 3: Update notion_tasks.sync_status column to use old type
    # Map 'success' -> 'done' during downgrade
    op.execute("""
        ALTER TABLE notion_tasks 
        ALTER COLUMN sync_status TYPE syncstatus 
        USING CASE 
            WHEN sync_status::text = 'success' THEN 'done'::syncstatus
            ELSE sync_status::text::syncstatus
        END
    """)
    
    # Step 4: Update caldav_events.sync_status column to use old type
    # Map 'success' -> 'done' during downgrade
    op.execute("""
        ALTER TABLE caldav_events 
        ALTER COLUMN sync_status TYPE syncstatus 
        USING CASE 
            WHEN sync_status::text = 'success' THEN 'done'::syncstatus
            ELSE sync_status::text::syncstatus
        END
    """)
    
    # Step 5: Drop new enum type
    op.execute("DROP TYPE syncstatus_new")
    
    # Step 6: Set default values using the old enum
    op.alter_column('notion_tasks', 'sync_status', server_default=sa.text("'pending'::syncstatus"))
    op.alter_column('caldav_events', 'sync_status', server_default=sa.text("'pending'::syncstatus"))

