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
    sync_service = SyncService(user_id=7)
    orm = CalDavORM(user_id=7)
    await orm.authenticate()

    # Получаем календарь
    calendar = await orm.Calendar.get_by_name("Personal")

    # Весь async код выполняем внутри одной сессии
    # Пример soft-delete задачи
    try:
        result = await notion_task_repo.delete(
            user_id=7,
            page_id="64f90cc8-6926-4dcf-b9da-13a8c145936c"
        )
        if result:
            logger.info("Task soft-deleted successfully")
        else:
            logger.info("Task not found for soft-deletion")
    except Exception as e:
        logger.error(f"Failed to delete task: {e}")

        # Пример синхронизации CalDAV (можешь раскомментировать)
        # await sync_service.sync_caldav_to_db(user_id=7, calendar_name="Personal", db=db)

if __name__ == "__main__":
    from server.services.scheduler.scheduler_service import sync_caldav_to_db_for_all_users
    asyncio.run(sync_caldav_to_db_for_all_users())