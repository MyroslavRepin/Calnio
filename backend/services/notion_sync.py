from backend.services.crud.tasks import delete_pages_by_ids, add_tasks_to_db, update_pages_by_ids
import logging
from notion_client import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.utils.notion.utils import get_all_ids


async def notion_sync_background(db: AsyncSession, notion: AsyncClient, user_id: int):
    print(f"[Background] notion_sync_background started for user_id={user_id}")

    added = await add_tasks_to_db(db, notion=notion, user_id=user_id)

    current_notion_pages = await get_all_ids(notion=notion)

    deleted = await delete_pages_by_ids(db, notion, user_id, current_notion_pages)
    updated = await update_pages_by_ids(db, notion, user_id, current_notion_pages)
    logging.info(f"[Background] notion_sync_background finished for user_id={user_id}")
    return {
        "added": added,
        "deleted": deleted,
        "updated": updated
    }
