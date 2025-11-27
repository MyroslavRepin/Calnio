import os
import sys
import asyncio

from server.db.deps import async_get_db_cm

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from server.db.repositories.notion_tasks import NotionTaskRepository
from server.services.caldav.utils.caldav_orm import CalDavORM
from server.services.sync.sync_manager import SyncService
from server.app.core.logging_config import logger

async def main():
    # Создаем репозитории и сервисы
    notion_task_repo = NotionTaskRepository()
    sync_service = SyncService(user_id=3)
    orm = CalDavORM(user_id=3)
    await orm.authenticate()

    # Получаем календарь
    calendar = await orm.Calendar.get_by_name("Work")
    "00:49:23+00:00"
    "00:49:23+00:00"
    # events = calendar.events()
    #
    # logger.info(f"Events: {events}")

    async with async_get_db_cm() as db:
        await sync_service.sync_caldav_to_db(user_id=3, calendar=calendar, db=db)

if __name__ == "__main__":
    asyncio.run(main())