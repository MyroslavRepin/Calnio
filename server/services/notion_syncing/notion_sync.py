import json

from server.app.schemas.notion_pages import NotionTask
from server.db.deps import async_get_db_cm
from server.db.models import User
from server.db.models.tasks import UserNotionTask
from server.db.redis_client import get_redis
from server.integrations.notion.notion_client import get_notion_client
from server.db.repositories.notion_tasks import NotionTaskRepository
from server.utils.notion.utils import get_all_ids
from server.utils.decorators import timer
from server.utils.redis.utils import get_webhook_data
from server.app.core.logging_config import logger

from notion_client import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload


async def notion_sync_background(db: AsyncSession, notion: AsyncClient, user_id: int):

    # Check if active_sync is still True and get user's database_id
    stmt = select(User).options(selectinload(User.notion_integration)).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        logger.error(f"User {user_id} not found")
        return {"added": [], "deleted": {"deleted_pages": []}, "updated": []}

    if not user.active_sync:
        logger.info(f"Sync is not active for user_id={user_id}, skipping sync")
        return {"added": [], "deleted": {"deleted_pages": []}, "updated": []}

    # Get the database_id from the integration
    database_id = None
    if user.notion_integration:
        database_id = user.notion_integration.duplicated_template_id
        if database_id:
            logger.info(f"Using database_id={database_id} for user_id={user_id}")
        else:
            logger.warning(f"No database_id found for user_id={user_id}, will search all databases")
    else:
        logger.warning(f"No notion_integration found for user_id={user_id}")

    logger.info(f"Background sync started for user_id={user_id}")

    Task = NotionTaskRepository()

    # Step 1: Add new tasks from Notion
    logger.info(f"Step 1: Adding new tasks for user_id={user_id}")
    added = await Task.add_tasks_to_db(notion=notion, user_id=user_id, last_modified_source="notion", sync_source="background", database_id=database_id)
    logger.info(f"Added {len(added)} new tasks for user_id={user_id}")

    # Step 2: Delete tasks that no longer exist in Notion
    logger.info(f"Step 2: Checking for deleted tasks for user_id={user_id}")
    current_notion_pages = await get_all_ids(notion=notion, database_id=database_id)
    deleted = await Task.delete_pages_by_ids(notion, user_id, current_notion_pages)
    logger.info(f"Deleted {len(deleted.get('deleted_pages', []))} tasks for user_id={user_id}")

    # Step 3: Update existing tasks
    logger.info(f"Step 3: Updating existing tasks for user_id={user_id}")
    updated = await Task.update_pages_by_ids(notion, user_id, current_notion_pages, sync_source="background", last_modified_source="notion")
    logger.info(f"Updated {len(updated)} tasks for user_id={user_id}")

    logger.info(f"Background sync finished for user_id={user_id}")

    return {
        "added": added,
        "deleted": deleted,
        "updated": updated
    }

async def db_to_notion_sync(db: AsyncSession, user_id):
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
                # Update existing Notion page (PATCH)
                await notion.pages.update(page_id=page_id, properties=properties)
            else:
                # Create new Notion page (POST)
                database_id = getattr(user.notion_integration, "database_id", None)
                if not database_id:
                    logger.warning(f"No Notion database_id for user_id={user_id}; skipping create for task_id={task.id}")
                    continue

                await notion.pages.create(parent={"database_id": database_id}, properties=properties)
