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


    # await orm.Calendar.create(title="Test Calendar 2")
    calendar = await orm.Calendar.get(uid="f6492090-aaae-11f0-b31d-a2b363ae323e")

    delete_cal = await orm.Calendar.delete(calendar)
    print(delete_cal)
if __name__ == "__main__":
    asyncio.run(main())