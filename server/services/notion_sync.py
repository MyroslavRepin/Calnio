from server.db.deps import async_get_db_cm
from server.db.models import User
from server.services.crud.tasks import delete_pages_by_ids, add_tasks_to_db, update_pages_by_ids
from server.utils.notion.utils import get_all_ids
from server.utils.decorators import timer
from server.utils.redis.utils import get_webhook_data
from server.app.core.logging_config import logger

from notion_client import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


async def notion_sync_background(db: AsyncSession, notion: AsyncClient, user_id: int):
    added = await add_tasks_to_db(db, notion=notion, user_id=user_id, last_modified_source="notion", sync_source="background")

    # Check if active_sync is still True

    # AsyncSession made out of HTTP
    async with async_get_db_cm() as db:
        stmt = select(User.active_sync).where(User.id == user_id)
        result = await db.execute(stmt)
        active_sync = result.scalars().first()
        if not active_sync:
            logger.info(f"Background sync not started for user_id={user_id} (active_sync=False)")
            return {"added": added}

    logger.info(f"Background sync started for user_id={user_id}")


    current_notion_pages = await get_all_ids(notion=notion)
    deleted = await delete_pages_by_ids(db, notion, user_id, current_notion_pages)
    updated = await update_pages_by_ids(db, notion, user_id, current_notion_pages, sync_source="background", last_modified_source="notion")
    logger.info(f"Background sync finished for user_id={user_id}")

    return {
        "added": added,
        "deleted": deleted,
        "updated": updated
    }


async def webhook_sync():
    webhook_data = await get_webhook_data()
    page_id = webhook_data["page_id", [None]]

    if page_id:
        # Start syncing just for one page
        ...
