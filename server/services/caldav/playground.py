import os
import sys
import asyncio
from datetime import datetime, timezone

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from server.db.repositories.notion_tasks import NotionTaskRepository
from server.services.caldav.caldav_orm import CalDavORM
from server.db.deps import async_get_db_cm
from server.services.sync.sync_manager import SyncService
from server.app.core.logging_config import logger

async def main():
    # Создаем репозитории и сервисы
    notion_task_repo = NotionTaskRepository()
    sync_service = SyncService(user_id=3)
    orm = CalDavORM(user_id=3)
    await orm.authenticate()

    # Получаем календарь
    calendar = await orm.Calendar.get_by_name("Personal")

    async with async_get_db_cm() as db:
        await sync_service.sync_user_events(user_id=3, calendar_name="Personal", db=db)

if __name__ == "__main__":
    asyncio.run(main())