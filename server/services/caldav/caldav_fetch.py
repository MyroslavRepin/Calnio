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

from server.services.caldav.caldav_client import get_caldav_client
from server.app.core.logging_config import logger
from server.services.crud.caldav_events import CalDavEvent, get_caldav_tasks


async def main():
    user_id = 7
    logger.info("🔗 Connecting to CalDAV...")

    client = await get_caldav_client(user_id=user_id)
    principal = await client.principal()
    calendars = await principal.calendars()

    if not calendars:
        logger.warning("❌ No calendars found")
        return

    logger.info("📂 YOUR CALENDARS:")
    for i, cal in enumerate(calendars, 1):
        logger.info(f"{i}. {getattr(cal, 'name', 'Unnamed')} - {cal.url}")

    # Ищем Personal календарь
    personal_cal = next((cal for cal in calendars if "Personal" in cal.name), None)
    if personal_cal is None:
        logger.error("No Personal calendar found")
        return

    # Создаём событие
    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(hours=2)

    tasks = []
    for item in await calendar.items():
        task = await CalDavEvent.from_item(calendar, item)
        if task:
            tasks.append(task)


if __name__ == "__main__":
    asyncio.run(main())