# Deleted Events Detection - Usage Guide

## Overview

This module provides functionality to detect and handle events that have been deleted from iCloud CalDAV but still exist in the local database.

## Functions

### `get_deleted_events_from_caldav(calendar, db)`

Detects events that exist locally but have been deleted from the remote CalDAV server.

**Parameters:**
- `calendar`: CalDAV calendar object from iCloud
- `db`: AsyncSession for database operations

**Returns:**
- `list[dict]`: List of deleted events with the following structure:
  ```python
  {
      "caldav_uid": "unique-event-id.ics",
      "title": "Event Title",
      "deleted_at": datetime(2025, 11, 27, ...),
      "local_event": CalDavEvent  # SQLAlchemy object
  }
  ```

**How it works:**
1. Fetches all non-deleted events from local database for the user
2. Fetches all events from the remote CalDAV calendar
3. Compares UIDs between local and remote
4. Returns events that exist locally but not remotely

### `mark_events_as_deleted(deleted_events, db)`

Marks detected deleted events in the database.

**Parameters:**
- `deleted_events`: List of deleted event dicts from `get_deleted_events_from_caldav`
- `db`: AsyncSession for database operations

**Returns:**
- `int`: Number of events successfully marked as deleted

**What it does:**
- Sets `deleted=True` for each event
- Sets `deleted_at` timestamp
- Commits changes to database
- Handles errors gracefully

## Usage Example

```python
from server.services.sync.sync_manager import SyncService
from server.db.deps import async_get_db_cm

async def sync_and_handle_deletions(user_id: int):
    """Complete example of detecting and handling deleted events."""
    
    # Initialize sync service
    sync_service = SyncService(user_id=user_id)
    await sync_service.caldav_orm.authenticate()
    
    # Get the calendar
    calendar = await sync_service.caldav_orm.Calendar.get_by_name("Personal")
    
    if not calendar:
        logger.error("Calendar not found")
        return
    
    # Get database session
    async with async_get_db_cm() as db:
        # Step 1: Detect deleted events
        deleted_events = await sync_service.get_deleted_events_from_caldav(
            calendar=calendar,
            db=db
        )
        
        # Step 2: Log what we found
        logger.info(f"Found {len(deleted_events)} deleted events")
        for event in deleted_events:
            logger.info(f"- {event['title']} (UID: {event['caldav_uid']})")
        
        # Step 3: Mark events as deleted in database
        if deleted_events:
            marked_count = await sync_service.mark_events_as_deleted(
                deleted_events=deleted_events,
                db=db
            )
            logger.info(f"Successfully marked {marked_count} events as deleted")
```

## Integration with Sync Flow

```python
async def full_sync_with_deletion_handling(user_id: int, calendar, db: AsyncSession):
    """Example of integrating deletion detection into sync flow."""
    
    sync_service = SyncService(user_id=user_id)
    
    # 1. Detect and handle deletions first
    deleted_events = await sync_service.get_deleted_events_from_caldav(calendar, db)
    if deleted_events:
        await sync_service.mark_events_as_deleted(deleted_events, db)
    
    # 2. Then proceed with regular sync
    await sync_service.sync_caldav_to_db(user_id, calendar, db)
    
    # 3. Sync other direction if needed
    await sync_service.sync_db_to_caldav()
```

## Modern CalDAV Best Practices

This implementation follows modern CalDAV sync practices:

1. **UID Comparison**: Uses event UIDs (unique identifiers) for comparison
2. **Async Operations**: All CalDAV operations run in separate threads to avoid blocking
3. **Soft Deletes**: Marks events as deleted rather than removing them from DB
4. **Error Handling**: Graceful error handling with detailed logging
5. **Timezone Aware**: Uses UTC timestamps for deletion times

## Notes

- Events are soft-deleted (marked with `deleted=True`) rather than removed from the database
- This preserves audit trail and allows for potential recovery
- The function only checks non-deleted local events to avoid redundant checks
- Remote CalDAV fetching is done in a thread to prevent blocking the async event loop

