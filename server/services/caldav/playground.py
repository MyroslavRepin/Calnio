import asyncio
import calendar
from datetime import datetime, timedelta, timezone
import os
import sys
import uuid
from urllib.parse import urlparse

from aiocaldav import Calendar

# Ensure project root is on sys.path when running this file directly
if __name__ == "__main__":
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)

from server.services.caldav.caldav_orm import CalDavORM
from server.utils.utils import extract_uid
from server.services.caldav.user_calendars import sync_user_calendars
from server.db.repositories.caldav_events import CaldavEventsRepository
from server.db.deps import async_get_db_cm
from server.services.sync.sync_manager import SyncService
from server.app.core.logging_config import logger
import pretty_errors



async def main():
    async with async_get_db_cm() as db:
        caldav_repo = CaldavEventsRepository()
        sync_service = SyncService(user_id=7)

    orm = CalDavORM(user_id=7)
    await orm.authenticate()

    calendar = await orm.Calendar.get_by_name("Personal")

    # await sync_user_calendars()
    # await sync_user_events()
    # caledar_uid = extract_uid(calendar.id)
    # This code should save all events from the calendar to the database
    # The problem that it syncs from db to CalDav too, with duplicates too
    # await orm.Event.save_from_caldav(calendar_uid=caledar_uid, user_id=7)

    # await caldav_repo.sync_user_events()
    # await caldav_repo.sync_caldav_to_db(user_id=7, calendar_name="Personal")


    # Fixme: It working, but need to make checking for duplicates
    # calendar = await orm.Calendar.get_by_name("Personal")

    # event_url = extract_uid("https://p48-caldav.icloud.com:443/21349328538/calendars/966BC571-A000-4BC6-85DA-11A2EDA6156E/ee191ec8-af79-11f0-8153-a2b363ae323f.ics")
    # logger.debug(f"Event URL: {event_url}")
    # exists = await orm.Event.exists(calendar=calendar, event_uid=event_url)
    # logger.debug(f"Function 'exists': {exists}")

    # exists = await orm.Event.get()

    # events = await orm.Event.all(calendar_uid=extract_uid(calendar.id))
    # for event in events:
    #     logger.debug(event.url)


    # await sync_service.sync_db_to_caldav()
    async with async_get_db_cm() as db:
        # await sync_service.sync_caldav_to_db(user_id=7, calendar_name="Personal", db=db)

        deleted_events = await orm.Event.get_deleted_events(calendar=calendar, db=db, user_id=7)
        logger.info(f"Deleted events: {deleted_events}")


    # event_uid =  "70b22548ef8544f88d84f33f47f3cc33".lower()
    # logger.info(event_uid)
    # events = await orm.Event.all(calendar_uid=extract_uid(calendar.id))
    # for event in events:
    #     logger.info(extract_uid(event.url))
    # # logger.info(events)
    # # event = await orm.Event.get(name="Specific test event", calendar=calendar)
    # # logger.info(event)
    # event_uid = "e5e1df7d-fea0-41c4-abad-7aa28c8c1aff.ics"
    # event = await orm.Event.get(event_uid=event_uid, calendar=calendar)
    # logger.info(f"Event by id: {event}")

if __name__ == "__main__":
    asyncio.run(main())