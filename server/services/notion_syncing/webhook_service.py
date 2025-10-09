from server.app.schemas.notion_pages import NotionTask
from server.db.deps import async_get_db_cm
from server.db.models import User
from server.integrations.notion.notion_client import get_notion_client
from server.utils.notion.utils import to_utc_datetime, normalize_notion_id
from server.utils.redis.utils import get_webhook_data
from server.db.redis_client import get_redis
from server.services.crud.tasks import create_task, delete_task
from server.app.core.logging_config import logger

from sqlalchemy import select

async def sync_webhook_data():
    logger.info("Starting webhook sync")
    redis_client = await get_redis()
    webhook_data = await get_webhook_data(redis=redis_client, user_id=7)

    user_id = webhook_data["user_id"]
    page_id_raw = webhook_data["page_id"]
    event_type = webhook_data["event_type"]

    # Normalize page_id by removing dashes
    page_id = normalize_notion_id(page_id_raw)

    logger.debug(f"Webhook event: {event_type}")
    logger.debug(f"   User ID: {user_id}")
    logger.debug(f"   Page ID (raw): {page_id_raw}")
    logger.debug(f"   Page ID (normalized): {page_id}")

    async with async_get_db_cm() as db:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user:
            logger.error(f"User with id {user_id} not found")
            return {"error": f"User {user_id} not found"}

        # Handle page deletion - don't fetch page data from Notion
        if event_type == "page.deleted":
            logger.info(f"Processing deletion for page_id: {page_id}")
            deleted = await delete_task(db=db, user_id=user_id, page_id=page_id)
            if deleted:
                logger.info(f"Task deleted successfully")
            else:
                logger.warning(f"Task not found in database (might have been already deleted)")
            return {"message": "Task deleted", "page_id": page_id}

        # Handle page creation and updates - fetch page data from Notion
        if event_type in ["page.created", "page.properties_updated"]:
            try:
                logger.info(f"Fetching page data from Notion API...")
                notion_client = get_notion_client(user.notion_integration.access_token)
                # Use raw page_id with dashes for Notion API
                page = await notion_client.pages.retrieve(page_id=page_id_raw)
                notion_page = NotionTask.from_notion(page)

                start_date_utc = to_utc_datetime(notion_page.start_date)
                end_date_utc = to_utc_datetime(notion_page.end_date)

                logger.info(f"Task from Notion: '{notion_page.title}'")

                # create_task handles both create and update (upsert)
                # Use normalized page_id without dashes for database
                task = await create_task(
                    db=db,
                    user_id=user_id,
                    title=notion_page.title,
                    notion_page_id=page_id,
                    notion_url=notion_page.notion_page_url,
                    sync_source="notion",
                    description=notion_page.description,
                    caldav_uid="not supported yet",
                    has_conflict=False,
                    last_modified_source="notion",
                    start_date=start_date_utc,
                    end_date=end_date_utc,
                    status=notion_page.status,
                    done=notion_page.done,
                    priority=notion_page.priority,
                    select_option=notion_page.select_option,
                )

                action = "updated" if event_type == "page.properties_updated" else "created"
                logger.info(f"Webhook sync complete: Task {action}")

            except Exception as e:
                logger.error(f"Error processing {event_type} for page {page_id}: {e}", exc_info=True)
                raise

        else:
            logger.warning(f"Unknown event type: {event_type}")
            return {"error": f"Unknown event type: {event_type}"}

    logger.info(f"Webhook sync finished successfully")
    return {"message": "Webhook data synced", "event_type": event_type, "page_id": page_id}
