# PostgreSQL ENUM Type Guide for sync_status

## Overview
This guide explains how to properly work with the `syncstatus` PostgreSQL ENUM type to avoid operator mismatch errors.

## The Problem
When migrating a column from VARCHAR to ENUM in PostgreSQL, you may encounter:
```
[42883] ERROR: operator does not exist: syncstatus = character varying
Hint: No operator matches the given name and argument types. You might need to add explicit type casts.
```

This happens because PostgreSQL doesn't have an operator `=` defined between enum and varchar types.

## Root Causes

1. **SQLAlchemy binding parameters as VARCHAR**: If SQLAlchemy models don't use `postgresql.ENUM` with `native_enum=True`, parameters are bound as varchar instead of the enum type.

2. **Functions/Triggers with varchar parameters**: Database functions or triggers that accept text/varchar parameters and compare them to enum columns will fail.

3. **String literals without type cast**: Using string literals like `'pending'` instead of `'pending'::syncstatus` in SQL.

## Solutions

### 1. SQLAlchemy Model Configuration

**Correct way** - Use `postgresql.ENUM` with `native_enum=True`:

```python
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from server.db.models.enums import SyncStatus

class UserNotionTask(Base):
    __tablename__ = "notion_tasks"
    
    sync_status: Mapped[SyncStatus] = mapped_column(
        PGEnum(SyncStatus, name='syncstatus', native_enum=True),
        default=SyncStatus.pending,
        nullable=False
    )
```

**Incorrect way** - Using generic SQLAlchemy Enum:
```python
from sqlalchemy import Enum

# ❌ This binds parameters as VARCHAR
sync_status = mapped_column(Enum(SyncStatus))
```

### 2. PL/pgSQL Enum Comparisons

#### Option A: Cast string literal to enum (recommended)
```sql
-- In PL/pgSQL function or trigger
IF NEW.sync_status = 'success'::syncstatus THEN
    -- do something
END IF;

-- In WHERE clause
UPDATE notion_tasks 
SET title = 'Updated' 
WHERE sync_status = 'pending'::syncstatus;
```

#### Option B: Cast enum column to text
```sql
-- In PL/pgSQL function or trigger
IF NEW.sync_status::text = 'success' THEN
    -- do something
END IF;

-- In WHERE clause
UPDATE notion_tasks 
SET title = 'Updated' 
WHERE sync_status::text = 'pending';
```

**Important**: Option A (casting literal to enum) is preferred because:
- It maintains type safety
- PostgreSQL can use indexes on the enum column
- It prevents invalid enum values at compile time

### 3. Function Parameter Types

**Correct** - Use enum type for parameters:
```sql
CREATE OR REPLACE FUNCTION update_task_status(
    task_id varchar,
    new_status syncstatus  -- ✅ Use enum type
) RETURNS void AS $$
BEGIN
    UPDATE notion_tasks 
    SET sync_status = new_status
    WHERE id = task_id;
END;
$$ LANGUAGE plpgsql;
```

**Incorrect** - Using text/varchar parameters:
```sql
CREATE OR REPLACE FUNCTION update_task_status(
    task_id varchar,
    new_status varchar  -- ❌ Causes operator mismatch
) RETURNS void AS $$
BEGIN
    UPDATE notion_tasks 
    SET sync_status = new_status  -- ERROR: syncstatus = character varying
    WHERE id = task_id;
END;
$$ LANGUAGE plpgsql;
```

If you must use varchar parameter, cast it:
```sql
CREATE OR REPLACE FUNCTION update_task_status(
    task_id varchar,
    new_status varchar
) RETURNS void AS $$
BEGIN
    UPDATE notion_tasks 
    SET sync_status = new_status::syncstatus  -- ✅ Cast varchar to enum
    WHERE id = task_id;
END;
$$ LANGUAGE plpgsql;
```

### 4. Trigger Examples

**Example trigger with proper enum handling:**

```sql
CREATE OR REPLACE FUNCTION set_sync_status_trigger()
RETURNS TRIGGER AS $$
BEGIN
    -- Compare using enum-cast literal
    IF NEW.sync_source = 'caldav' AND NEW.sync_status::text != 'pending' THEN
        NEW.sync_status = 'pending'::syncstatus;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ensure_sync_status
    BEFORE INSERT OR UPDATE ON notion_tasks
    FOR EACH ROW
    EXECUTE FUNCTION set_sync_status_trigger();
```

### 5. Migration Best Practices

When migrating from VARCHAR to ENUM:

```python
def upgrade() -> None:
    # 1. Create the enum type
    op.execute("CREATE TYPE syncstatus AS ENUM ('pending', 'success', 'failed')")
    
    # 2. Alter column with explicit USING clause to convert values
    op.execute("""
        ALTER TABLE notion_tasks 
        ALTER COLUMN sync_status TYPE syncstatus 
        USING sync_status::syncstatus
    """)
    
    # 3. Set default using enum-cast literal
    op.alter_column('notion_tasks', 'sync_status', 
                    server_default=sa.text("'pending'::syncstatus"))
    
    # 4. Update any functions/triggers that reference this column
    op.execute("DROP FUNCTION IF EXISTS old_function CASCADE")
    op.execute("""
        CREATE FUNCTION new_function(status syncstatus) 
        RETURNS void AS $$ ... $$ LANGUAGE plpgsql
    """)
```

## syncstatus Enum Values

The `syncstatus` enum type has the following valid values:
- `'pending'` - Task is waiting to be synchronized
- `'success'` - Task was successfully synchronized
- `'failed'` - Task synchronization failed

## Testing Your Changes

After updating to use proper enum types, verify:

1. **Check enum type exists:**
```sql
SELECT typname, enumlabel 
FROM pg_type t 
JOIN pg_enum e ON t.oid = e.enumtypid 
WHERE typname = 'syncstatus'
ORDER BY e.enumsortorder;
```

2. **Check column types:**
```sql
SELECT column_name, data_type, udt_name
FROM information_schema.columns
WHERE table_name = 'notion_tasks' AND column_name = 'sync_status';
```

3. **Test insert/update from Python:**
```python
from server.db.models.enums import SyncStatus

# This should work without errors
task.sync_status = SyncStatus.success
await db.commit()
```

## Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `operator does not exist: syncstatus = character varying` | SQLAlchemy binding as varchar OR function parameter is varchar | Use `postgresql.ENUM(..., native_enum=True)` in model AND ensure function parameters are `syncstatus` type |
| `invalid input value for enum syncstatus: "done"` | Trying to use a value not in the enum definition | Update enum type to include the value OR map old value to new one in migration |
| `type "syncstatus" does not exist` | Enum type not created in database | Run migration to create enum type |
| `column "sync_status" is of type syncstatus but expression is of type text` | Assignment without type cast | Cast the value: `'pending'::syncstatus` |

## Summary

✅ **DO:**
- Use `postgresql.ENUM(..., native_enum=True)` in SQLAlchemy models
- Cast string literals to enum: `'pending'::syncstatus`
- Define function parameters as enum type: `status syncstatus`
- Use `USING` clause when altering column type in migrations

❌ **DON'T:**
- Use generic `sqlalchemy.Enum()` for PostgreSQL enum columns
- Compare enum columns with uncast string literals
- Define function parameters as `text` or `varchar` when working with enum columns
- Forget to update functions/triggers after changing column to enum type
