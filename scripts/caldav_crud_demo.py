import asyncio
from datetime import datetime, timedelta, timezone

from server.services.caldav import get_caldav_client
from server.services.crud.caldav_events import (
    create_event,
    delete_event_by_uid,
    get_all_events,
    get_all_events_ids,
    get_event_by_uid,
    mark_todo_completed,
    update_event,
)
from server.app.core.logging_config import logger


async def run(user_id: int = 1):
    client = await get_caldav_client(user_id=user_id)
    principal = await client.principal()
    calendars = await principal.calendars()

    if not calendars:
        logger.error("No calendars found")
        return

    # Pick first calendar or Personal
    calendar = next((c for c in calendars if 'Personal' in getattr(c, 'name', '')), calendars[0])
    logger.info(f"Using calendar: {getattr(calendar, 'name', 'Unnamed')} - {calendar.url}")

    # Create an event
    start = datetime.now(timezone.utc) + timedelta(minutes=2)
    end = start + timedelta(hours=1)
    ev = await create_event(calendar, title="Calnio Demo Event", start_date=start, end_date=end)
    logger.info(f"Created event UID: {ev.model.uid}")

    # List events ids
    ids = await get_all_events_ids(calendar, months=1)
    logger.info(f"IDs in window: {ids[:5]}{'...' if len(ids) > 5 else ''}")

    # Fetch by uid
    fetched = await get_event_by_uid(calendar, ev.model.uid)
    logger.info(f"Fetched by UID: {fetched.model.title if fetched else None}")

    # Update title
    await update_event(calendar, ev.model.uid, title="Calnio Demo Event (Updated)")

    # Mark todo complete example (will no-op for VEVENT)
    await mark_todo_completed(calendar, ev.model.uid)

    # List all events in window
    events = await get_all_events(calendar, months=1)
    logger.info(f"Found {len(events)} events in ±1 month")

    # Cleanup
    await delete_event_by_uid(calendar, ev.model.uid)
    logger.info("Deleted demo event")


if __name__ == "__main__":
    asyncio.run(run())

