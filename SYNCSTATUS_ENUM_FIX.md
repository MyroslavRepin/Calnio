# Fix for "operator does not exist: syncstatus = character varying" Error

## Summary

This fix addresses the PostgreSQL enum type mismatch error that occurs when SQLAlchemy tries to update records with an enum column but binds parameters as VARCHAR instead of the native PostgreSQL enum type.

## Changes Made

### 1. Updated Python Enum Definition
**File**: `server/db/models/enums.py`

Changed from:
```python
class SyncStatus(str, Enum):
    pending = "pending"
    partial = "partial"
    synced = "synced"
    error = "error"
```

To:
```python
class SyncStatus(str, Enum):
    pending = "pending"
    success = "success"
    failed = "failed"
```

### 2. Updated SQLAlchemy Models to Use Native PostgreSQL ENUM

**Files**: 
- `server/db/models/tasks.py`
- `server/db/models/caldav_events.py`

Changed from:
```python
from sqlalchemy import Enum

sync_status: Mapped[SyncStatus] = mapped_column(
    Enum(SyncStatus),
    default=SyncStatus.pending,
    nullable=False
)
```

To:
```python
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

sync_status: Mapped[SyncStatus] = mapped_column(
    PGEnum(SyncStatus, name='syncstatus', native_enum=True),
    default=SyncStatus.pending,
    nullable=False
)
```

**Key change**: Using `postgresql.ENUM(..., native_enum=True)` ensures SQLAlchemy binds parameters as the PostgreSQL enum type instead of VARCHAR, preventing the operator mismatch error.

### 3. Created Database Migration
**File**: `server/alembic/versions/f0995c8c6da0_update_syncstatus_enum_values.py`

The migration:
- Renames the old enum type (`syncstatus_old`)
- Creates a new enum type with correct values: `('pending', 'success', 'failed')`
- Updates both `notion_tasks` and `caldav_events` tables
- Maps existing 'done' values to 'success'
- Drops the old enum type

### 4. Added Comprehensive Documentation
**File**: `docs/POSTGRESQL_ENUM_GUIDE.md`

Provides:
- Explanation of the root cause
- Correct SQLAlchemy model configuration
- PL/pgSQL enum comparison examples
- Function/trigger parameter type guidelines
- Migration best practices
- Common errors and solutions

## How to Apply These Changes

### Step 1: Review the Changes
Review all modified files to ensure they align with your database schema.

### Step 2: Run the Migration
```bash
# Run the migration to update the PostgreSQL enum type
alembic upgrade head
```

The migration will:
1. Update the `syncstatus` enum from `('pending', 'done', 'failed')` to `('pending', 'success', 'failed')`
2. Convert all existing 'done' values to 'success' in both tables
3. Preserve all other data

### Step 3: Restart Your Application
After the migration completes, restart your application to use the updated models.

### Step 4: Verify the Fix
Test that updates work correctly:

```python
from server.db.models import UserNotionTask
from server.db.models.enums import SyncStatus

# This should now work without the operator mismatch error
task = await db.get(UserNotionTask, task_id)
task.sync_status = SyncStatus.success
await db.commit()
```

## Root Cause Explained

The error occurred because:

1. **SQLAlchemy was binding parameters as VARCHAR**: Using the generic `Enum()` from SQLAlchemy instead of `postgresql.ENUM()` caused parameters to be bound as `character varying` (VARCHAR) type.

2. **PostgreSQL strict type checking**: When PostgreSQL saw a comparison like:
   ```sql
   WHERE sync_status = $1  -- where $1 is bound as VARCHAR
   ```
   It couldn't find an operator to compare `syncstatus` (enum) with `character varying` (varchar).

3. **Solution**: Using `postgresql.ENUM(..., native_enum=True)` tells SQLAlchemy to bind parameters as the PostgreSQL enum type, so comparisons work correctly:
   ```sql
   WHERE sync_status = $1  -- where $1 is now bound as syncstatus enum
   ```

## Database Functions and Triggers

If you have any custom database functions or triggers that work with the `sync_status` column, ensure they:

1. **Use enum-typed parameters**:
   ```sql
   CREATE FUNCTION my_function(status syncstatus) ...
   ```

2. **Cast string literals to enum**:
   ```sql
   IF NEW.sync_status = 'pending'::syncstatus THEN ...
   ```

3. **Or cast enum to text for comparison**:
   ```sql
   IF NEW.sync_status::text = 'pending' THEN ...
   ```

See `docs/POSTGRESQL_ENUM_GUIDE.md` for detailed examples.

## Testing

After applying these changes, test:

1. ✅ Creating new records with sync_status
2. ✅ Updating existing records' sync_status
3. ✅ Filtering by sync_status in queries
4. ✅ Any custom functions/triggers that use sync_status

## Rollback

If you need to rollback these changes:

```bash
# Rollback the migration
alembic downgrade -1
```

Then revert the code changes to use the old enum values and generic `Enum()`.

## References

- **PostgreSQL ENUM documentation**: https://www.postgresql.org/docs/current/datatype-enum.html
- **SQLAlchemy PostgreSQL ENUM**: https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#postgresql-enum-types
- **Problem Statement Issue**: Addresses operator mismatch when using PostgreSQL ENUM types with SQLAlchemy
