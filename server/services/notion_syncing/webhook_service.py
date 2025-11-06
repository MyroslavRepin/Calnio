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


async def sync_webhook_data(user_id: int = None):
    """
    Sync webhook data from Redis to database.
    Handles: page.created, page.properties_updated, page.deleted

    Args:
        user_id: The user ID to fetch webhook data for. If None, defaults to 7.

    Safely extracts webhook data from Redis and processes based on event type:
    - page.deleted: Deletes task from database
    - page.created: Creates task from Notion page
    - page.properties_updated: Updates task from Notion page
    """
    if user_id is None:
        user_id = 7  # Default fallback

    logger.info("=" * 80)
    logger.info(f"Starting webhook sync for user_id={user_id}")
    logger.info("=" * 80)

    # ========================================================================
    # Step 1: Get Redis client
    # ========================================================================
    try:
        redis_client = await get_redis()
        logger.debug("Redis client initialized")
    except Exception as e:
        logger.error(f"Failed to get Redis client: {e}")
        return {"error": "Redis connection failed"}

    # ========================================================================
    # Step 2: Fetch webhook data from Redis
    # ========================================================================
    try:
        webhook_data = await get_webhook_data(redis=redis_client, user_id=user_id)

        if not webhook_data:
            logger.warning(f"No webhook data found in Redis for user_id={user_id}")
            return {"error": "No webhook data found"}

        logger.debug(f"Webhook data retrieved from Redis for user_id={user_id}")
    except Exception as e:
        logger.error(f"Failed to get webhook data from Redis (user_id={user_id}): {e}")
        return {"error": "Failed to retrieve webhook data"}

    # ========================================================================
    # Step 3: Safely extract required fields
    # ========================================================================
    try:
        user_id = webhook_data.get("user_id")
        page_id_raw = webhook_data.get("page_id")
        event_type = webhook_data.get("event_type")

        # Validate required fields
        if not user_id:
            logger.error("Field 'user_id' missing from Redis webhook data")
            return {"error": "user_id missing"}

        if not page_id_raw:
            logger.error("Field 'page_id' missing from Redis webhook data")
            return {"error": "page_id missing"}

        if not event_type:
            logger.error("Field 'event_type' missing from Redis webhook data")
            event_type = "unknown"

        logger.info(f"Webhook data extracted: user_id={user_id}, event_type={event_type}")
    except Exception as e:
        logger.error(f"Failed to extract fields from webhook data: {e}", exc_info=True)
        return {"error": "Invalid webhook data structure"}

    # ========================================================================
    # Step 4: Keep page_id WITH dashes (original Notion UUID format)
    # ========================================================================
    # ⚠️  CRITICAL: Store notion_page_id WITH dashes for proper duplicate detection
    # Example: "284a5558-72b4-8086-82c3-da846290d940" (NOT normalized)
    page_id_with_dashes = page_id_raw
    logger.debug(f"Page ID (with dashes): {page_id_with_dashes}")

    # ========================================================================
    # Step 5: Get database connection and user
    # ========================================================================
    async with async_get_db_cm() as db:
        try:
            logger.debug(f"Querying User with id={user_id}")
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user = result.scalars().first()

            if not user:
                logger.error(f"User with id {user_id} not found in database")
                return {"error": f"User {user_id} not found"}

            logger.info(f"User found: id={user.id}, email={getattr(user, 'email', 'N/A')}")
        except Exception as e:
            logger.error(f"Database query failed for user_id={user_id}: {e}", exc_info=True)
            return {"error": "Database query failed"}

        # ====================================================================
        # Step 6: Handle page.deleted event
        # ====================================================================
        if event_type == "page.deleted":
            logger.info(f"Processing page.deleted for page_id: {page_id_with_dashes}")
            try:
                deleted = await delete_task(db=db, user_id=user_id, page_id=page_id_with_dashes)
                if deleted:
                    logger.info(f"✓ Task deleted successfully from database")
                    result_msg = {"message": "Task deleted", "page_id": page_id_with_dashes, "event_type": event_type}
                else:
                    logger.warning(f"Task not found in database (may have been already deleted)")
                    result_msg = {"message": "Task not found (already deleted?)", "page_id": page_id_with_dashes, "event_type": event_type}
                logger.info("=" * 80)
                return result_msg
            except Exception as e:
                logger.error(f"Failed to delete task: {e}", exc_info=True)
                return {"error": f"Delete failed: {str(e)}"}

        # ====================================================================
        # Step 7: Handle page.created and page.properties_updated
        # ====================================================================
        elif event_type in ["page.created", "page.properties_updated"]:
            try:
                # Get Notion client
                if not hasattr(user, 'notion_integration') or not user.notion_integration:
                    logger.error(f"User {user_id} has no Notion integration")
                    return {"error": "User has no Notion integration"}

                access_token = getattr(user.notion_integration, 'access_token', None)
                if not access_token:
                    logger.error(f"No access_token for user {user_id}")
                    return {"error": "No access token"}

                logger.info(f"Fetching page data from Notion API for page_id: {page_id_raw}")
                notion_client = get_notion_client(access_token)

                # Fetch page from Notion
                try:
                    page = await notion_client.pages.retrieve(page_id=page_id_raw)
                    logger.debug(f"Page retrieved from Notion API")
                except Exception as e:
                    logger.error(f"Failed to fetch page from Notion: {e}")
                    return {"error": f"Failed to fetch page from Notion: {str(e)}"}

                # Parse page data
                try:
                    notion_page = NotionTask.from_notion(page)
                    logger.info(f"Page parsed: title='{notion_page.title}'")
                except Exception as e:
                    logger.error(f"Failed to parse Notion page: {e}", exc_info=True)
                    return {"error": f"Failed to parse page: {str(e)}"}

                # Convert dates
                start_date_utc = to_utc_datetime(notion_page.start_date)
                end_date_utc = to_utc_datetime(notion_page.end_date)
                logger.debug(f"Dates converted: start={start_date_utc}, end={end_date_utc}")

                # Create or update task
                try:
                    logger.info(f"Creating/updating task in database")
                    task = await create_task(
                        db=db,
                        user_id=user_id,
                        title=notion_page.title,
                        notion_page_id=page_id_with_dashes,  # Pass WITH dashes for proper deduplication
                        notion_url=notion_page.notion_page_url,
                        sync_source="notion",
                        description=notion_page.description,
                        caldav_id="not supported yet",
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
                    logger.info(f"✓ Task {action} successfully in database (task_id={task.id})")

                    logger.info("=" * 80)
                    return {
                        "message": f"Task {action} successfully",
                        "event_type": event_type,
                        "page_id": page_id_with_dashes,
                        "task_id": task.id,
                    }
                except Exception as e:
                    logger.error(f"Failed to create/update task: {e}", exc_info=True)
                    return {"error": f"Task create/update failed: {str(e)}"}

            except Exception as e:
                logger.error(f"Error processing {event_type}: {e}", exc_info=True)
                return {"error": f"Processing failed: {str(e)}"}

        # ====================================================================
        # Step 8: Handle unknown event type
        # ====================================================================
        else:
            logger.warning(f"Unknown event type: {event_type}")
            logger.info("=" * 80)
            return {"error": f"Unknown event type: {event_type}"}


