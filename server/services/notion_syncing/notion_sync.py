import json

from server.app.schemas.notion_pages import NotionTask
from server.db.deps import async_get_db_cm
from server.db.models import User
from server.db.models.tasks import UserNotionTask
from server.db.redis_client import get_redis
from server.integrations.notion.notion_client import get_notion_client
from server.services.crud.tasks import delete_pages_by_ids, add_tasks_to_db, update_pages_by_ids, delete_task
from server.utils.notion.utils import get_all_ids
from server.utils.redis.utils import get_webhook_data
from server.app.core.logging_config import logger

from notion_client import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


async def notion_sync_background(db: AsyncSession, notion: AsyncClient, user_id: int):
    """
    Background sync: Fetch all Notion pages and sync with database
    Operations: CREATE new tasks, UPDATE existing tasks, DELETE removed tasks
    """
    logger.info(f"Background sync STARTED for user_id={user_id}")

    try:
        stmt = select(User.active_sync).where(User.id == user_id)
        result = await db.execute(stmt)
        active_sync = result.scalars().first()

        if not active_sync:
            logger.warning(f"Background sync not started for user_id={user_id} (active_sync=False)")
            return {"error": "active_sync is False", "added": [], "deleted": {}, "updated": []}

        logger.info(f"Starting sync for user_id={user_id}")

        logger.info(f"Adding new tasks from Notion")
        added = await add_tasks_to_db(
            db=db,
            notion=notion,
            user_id=user_id,
            last_modified_source="notion",
            sync_source="background"
        )
        logger.info(f"Added {len(added)} new tasks")

        logger.info(f"Fetching current pages from Notion")
        current_notion_pages = await get_all_ids(notion=notion)
        logger.info(f"Found {len(current_notion_pages)} pages in Notion")

        logger.info(f"Deleting removed tasks")
        deleted = await delete_pages_by_ids(db=db, notion=notion, user_id=user_id, pages_ids=current_notion_pages)
        logger.info(f"Deleted {len(deleted.get('deleted_pages', []))} tasks")

        logger.info(f"Updating existing tasks")
        updated = await update_pages_by_ids(
            db=db,
            notion=notion,
            user_id=user_id,
            pages_ids=current_notion_pages,
            sync_source="background",
            last_modified_source="notion"
        )
        logger.info(f"Updated {len(updated)} tasks")

        user = await db.execute(select(User).where(User.id == user_id))
        user_obj = user.scalars().first()
        if user_obj:
            user_obj.active_sync = False
            await db.commit()
            logger.info(f"Set active_sync=False for user_id={user_id}")

        logger.info(f"Background sync finished for user_id={user_id}")
        return {
            "status": "success",
            "added": added,
            "deleted": deleted,
            "updated": updated
        }

    except Exception as e:
        logger.error(f"❌ Background sync FAILED for user_id={user_id}: {e}", exc_info=True)
        # Set active_sync to False even on error
        try:
            user = await db.execute(select(User).where(User.id == user_id))
            user_obj = user.scalars().first()
            if user_obj:
                user_obj.active_sync = False
                await db.commit()
        except:
            pass

async def db_to_notion_sync(db: AsyncSession, user_id):
    async with async_get_db_cm() as db:
        stmt = select(UserNotionTask).where(UserNotionTask.user_id == user_id)
        stmt_user = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        result_user = await db.execute(stmt_user)
        tasks = result.scalars().all()
        user = result_user.scalars().first()

    notion = get_notion_client(user.notion_integration.access_token)
    redis = await get_redis()

    redis_data = await get_webhook_data(user_id, redis=redis)
    logger.debug(f"Redis data: {redis_data}")
    page = await notion.pages.retrieve(page_id="286a555872b48060981de81190e46319")
    logger.info(json.dumps(page, indent=2))
    for task in tasks:
        if task.sync_source not in ("notion", "background"):
            to_notion = NotionTask.to_notion(task=task)
            properties = to_notion.get("properties") or {}

            # Skip if there's nothing valid to update
            if not properties:
                logger.debug(f"No updatable properties for task_id={task.id}; skipping")
                continue

            page_id = getattr(task, "notion_page_id", None) or getattr(task, "page_id", None)

            if page_id:

                page_info = await notion.pages.retrieve(page_id=page_id)
                if page_info.get("archived", False):
                    logger.info(f"Page {page_id} is archived; deleting task_id={task.id} from DB")
                    await delete_task(db, page_id=task.id, user_id=user_id)  # функция удаления из БД
                    continue

                # Update existing Notion page (PATCH)
                await notion.pages.update(page_id=page_id, properties=properties)
            else:
                # Create new Notion page (POST)
                database_id = getattr(user.notion_integration, "database_id", None)
                if not database_id:
                    logger.warning(f"No Notion database_id for user_id={user_id}; skipping create for task_id={task.id}")
                    continue
                await notion.pages.create(parent={"database_id": database_id}, properties=properties)

