import asyncio
import calendar
from datetime import datetime, timedelta, timezone
import os
import sys
import uuid

from aiocaldav import Calendar

# Ensure project root is on sys.path when running this file directly
if __name__ == "__main__":
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)

from server.services.caldav.caldav_orm import CalDavORM

async def main():
    orm = CalDavORM(user_id=7)
    await orm.authenticate()

    calendars = await orm.Calendar.all()

    for cal in calendars:
        print(cal["uid"])

    result = await orm.Event.create(
        calendar_uid="D4536BB3-626F-4906-9129-FFACAD0D8736",
        title="Test Meeting",
        start="2025-10-15T15:00:00",
        end="2025-10-15T16:00:00",
        description="Project discussion"
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())