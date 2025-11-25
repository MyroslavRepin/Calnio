import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


from server.db.models.users import User
from server.db.models.caldav_events import CalDavEvent
from server.db.models.tasks import UserNotionTask
from server.db.models.notion_integration import UserNotionIntegration
from server.db.models.calendars import Calendar
from server.db.models.waitlist import Waitlist

from server.db.database import Base
from server.db.database import async_engine
import asyncio

async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(create_tables())