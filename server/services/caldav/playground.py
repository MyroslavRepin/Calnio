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
from server.services.caldav.user_events import sync_user_events


async def main():
    orm = CalDavORM(user_id=7)
    await orm.authenticate()

    calendar = await orm.Calendar.get_by_name("Personal")

    await orm.Event.create(
        calendar_uid=extract_uid(calendar.id),
        title="Test event",
        description="Test description",
        location="11324 91st",
        start=datetime.now(timezone.utc),
        end=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    # await sync_user_calendars()
    # await sync_user_events()
    caledar_uid = extract_uid(calendar.id)
    await orm.Event.save_from_caldav(calendar_uid=caledar_uid, user_id=7)

if __name__ == "__main__":
    asyncio.run(main())