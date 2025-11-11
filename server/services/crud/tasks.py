from server.app.core.logging_config import logger
from datetime import datetime, UTC
from notion_client import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.models.tasks import UserNotionTask
from server.app.schemas.notion_pages import NotionTask
from server.utils.notion.utils import get_all_ids, to_utc_datetime


async def create_task(
    db: AsyncSession,
    user_id: int,
    title: str,
    notion_page_id: str,
    notion_url: str,
    #
    sync_source: str,
    last_synced_at: datetime = None,
    caldav_id: str = None,
    has_conflict: bool = False,
    last_modified_source: str | None = None,
    #
    description: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    status: str | None = None,
    done: bool = False,
    priority: str | None = None,
    select_option: str | None = None,
) -> UserNotionTask:
    """
    Create or update a task based on notion_page_id.

    ⚠️  CRITICAL RULE: notion_page_id MUST be stored WITH DASHES (original Notion UUID)
    Example: "284a5558-72b4-8086-82c3-da846290d940" (NOT normalized without dashes)

    This function implements UPSERT logic:
    - If task exists by notion_page_id → UPDATE it (prevent duplicates)
    - If task doesn't exist → CREATE it

    This is the ONLY place where tasks are created/updated from webhooks and bulk sync.
    """
    # Store notion_page_id AS-IS with dashes - this is the Notion UUID (unique identifier)
    logger.debug(f"create_task: Checking for existing task with notion_page_id={notion_page_id}, user_id={user_id}")

    # Check if task already exists by BOTH notion_page_id AND user_id
    # This ensures each user has their own copy of the task
    stmt = select(UserNotionTask).where(
        UserNotionTask.notion_page_id == notion_page_id,
        UserNotionTask.user_id == user_id
    )
    result = await db.execute(stmt)
    existing_task = result.scalar_one_or_none()

    # Convert dates to UTC
    start_date_dt = to_utc_datetime(start_date)
    end_date_dt = to_utc_datetime(end_date)

    if existing_task:
        logger.info(
            f"Task exists, updating: task_id={existing_task.id}, notion_page_id={notion_page_id}"
        )
        logger.debug(f"Old title: {existing_task.title}")
        logger.debug(f"New title: {title}")

        existing_task.title = title
        existing_task.notion_url = notion_url
        existing_task.description = description
        existing_task.start_date = start_date_dt
        existing_task.end_date = end_date_dt
        existing_task.status = status
        existing_task.done = done
        existing_task.priority = priority
        existing_task.select_option = select_option
        existing_task.sync_source = sync_source
        existing_task.last_synced_at = datetime.now(UTC)
        existing_task.caldav_id = caldav_id if caldav_id else "not supported yet"
        existing_task.has_conflict = bool(has_conflict)
        existing_task.last_modified_source = last_modified_source

        await db.commit()
        await db.refresh(existing_task)
        logger.info(f"Task updated successfully: id={existing_task.id}")
        return existing_task

    logger.info(f"Creating new task: notion_page_id={notion_page_id}, title={title}")

    new_task = UserNotionTask(
        user_id=user_id,
        notion_page_id=notion_page_id,
        notion_url=notion_url,
        title=title,
        description=description,
        start_date=start_date_dt,
        end_date=end_date_dt,
        status=status,
        done=done,
        priority=priority,
        select_option=select_option,
        sync_source=sync_source,
        last_synced_at=datetime.now(UTC),
        caldav_id=caldav_id if caldav_id else "not supported yet",
        has_conflict=bool(has_conflict),
        last_modified_source=last_modified_source,
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    logger.info(f"Task created successfully: id={new_task.id}")
    return new_task


async def update_task(
    db: AsyncSession,
    task: UserNotionTask,
    title: str,
    notion_url: str,
    description: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    status: str | None = None,
    done: bool = False,
    priority: str | None = None,
    select_option: str | None = None,
    sync_source: str | None = None,
    last_modified_source: str | None = None
) -> UserNotionTask | None:
    """Update an existing task"""
    if task:
        task.title = title
        task.notion_url = notion_url
        task.description = description
        task.start_date = to_utc_datetime(start_date)
        task.end_date = to_utc_datetime(end_date)
        task.status = status
        task.done = done
        task.priority = priority
        task.select_option = select_option
        task.sync_source = sync_source
        task.last_synced_at = datetime.now(UTC)
        task.caldav_id = "not supported yet"
        task.has_conflict = False
        task.last_modified_source = last_modified_source
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task
    return None


async def delete_task(db: AsyncSession, user_id: int, page_id: str) -> bool:
    """
    Delete a task by notion_page_id and user_id.

    ⚠️  CRITICAL: page_id must be WITH DASHES (original Notion UUID format)
    Example: "284a5558-72b4-8086-82c3-da846290d940"

    Returns True if task was deleted, False if task was not found.
    """
    logger.debug(f"delete_task: Looking for task with notion_page_id={page_id}, user_id={user_id}")

    stmt = select(UserNotionTask).where(
        UserNotionTask.notion_page_id == page_id,
        UserNotionTask.user_id == user_id
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()

    if task:
        logger.info(f"✓ Deleting task (id={task.id}, notion_page_id={page_id})")
        await db.delete(task)
        await db.commit()
        logger.info(f"✓ Task deleted successfully")
        return True
    else:
        logger.warning(f"Task not found for deletion (notion_page_id={page_id}, user_id={user_id})")
        return False


# Syncing logics for each page separate (webhook)
async def sync_task_by_id(db: AsyncSession, notion: AsyncClient, user_id: int, page_id: str, event_type: str):
    """Sync a single task triggered by webhook event"""
    page = await notion.pages.retrieve(page_id=page_id)
    notion_page = NotionTask.from_notion(page)
    start_date_utc = to_utc_datetime(notion_page.start_date)
    end_date_utc = to_utc_datetime(notion_page.end_date)

    if event_type == "page.created":
        logger.info(f"Webhook: Creating task for new page: {page_id}")
        await create_task(
            db=db,
            user_id=user_id,
            title=notion_page.title,
            notion_url=notion_page.notion_page_url,
            sync_source="notion",
            notion_page_id=page_id,  # Pass WITH dashes
            description=notion_page.description,
            start_date=start_date_utc,
            end_date=end_date_utc,
            status=notion_page.status,
            select_option=notion_page.select_option,
            done=notion_page.done,
            priority=notion_page.priority
        )
    else:
        logger.info(f"Webhook: Received event '{event_type}' for page_id: {page_id}")


# Part of CRUD for all pages (bulk sync)
async def add_tasks_to_db(
    db: AsyncSession,
    user_id: int,
    notion: AsyncClient,
    sync_source: str,
    last_synced_at: datetime = None,
    caldav_id: str = None,
    has_conflict: bool = False,
    last_modified_source: str = "notion"
) -> list:
    """Bulk sync: fetch all pages from Notion and create/update tasks"""
    all_ids = await get_all_ids(notion=notion)
    added_pages = []

    for page_id in all_ids:
        logger.debug(f"Bulk sync: Processing page_id={page_id}")
        page = await notion.pages.retrieve(page_id=page_id)
        notion_page = NotionTask.from_notion(page)
        start_date_utc = to_utc_datetime(notion_page.start_date)
        end_date_utc = to_utc_datetime(notion_page.end_date)

        await create_task(
            db=db,
            user_id=user_id,
            notion_url=notion_page.notion_page_url,
            notion_page_id=page_id,  # Pass WITH dashes
            title=notion_page.title,
            description=notion_page.description,
            start_date=start_date_utc,
            end_date=end_date_utc,
            status=notion_page.status,
            select_option=notion_page.select_option,
            done=notion_page.done,
            priority=notion_page.priority,
            sync_source=sync_source,
            last_synced_at=last_synced_at,
            caldav_id=caldav_id,
            has_conflict=has_conflict,
            last_modified_source=last_modified_source
        )
        added_pages.append({
            "page_id": page_id,
            "title": notion_page.title,
            "status": "added"
        })
    return added_pages


async def delete_pages_by_ids(
        db: AsyncSession,
        notion: AsyncClient,
        user_id: int,
        pages_ids: list):
    """
    Delete tasks that no longer exist in Notion.
    Compare DB tasks with current Notion pages and delete missing ones.

    CRITICAL: pages_ids must contain Notion UUIDs WITH DASHES
    """
    logger.debug(f"Comparing {len(pages_ids)} Notion pages with DB tasks for user_id={user_id}")

    # Get all tasks for this user from database
    stmt = select(UserNotionTask).where(UserNotionTask.user_id == user_id)
    result = await db.execute(stmt)
    tasks = result.scalars().all()

    # Get notion_page_ids stored in DB (already WITH dashes)
    pages_ids_db = [task.notion_page_id for task in tasks]

    # pages_ids from Notion (WITH dashes)
    pages_ids_notion = pages_ids

    # Find pages in DB but NOT in Notion (these were deleted in Notion)
    pages_to_delete = list(set(pages_ids_db) - set(pages_ids_notion))

    logger.info(f"Found {len(pages_to_delete)} tasks to delete for user_id={user_id}")

    # Delete stale tasks
    for page_id in pages_to_delete:
        stmt = select(UserNotionTask).where(
            UserNotionTask.notion_page_id == page_id,
            UserNotionTask.user_id == user_id
        )
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()

        if task:
            logger.info(f"Deleting task id={task.id} for user_id={user_id}")
            await db.delete(task)

    await db.commit()
    logger.info(f"Deleted {len(pages_to_delete)} tasks for user_id={user_id}")
    return {"deleted_pages": pages_to_delete}


async def update_pages_by_ids(
        db: AsyncSession,
        notion: AsyncClient,
        user_id: int,
        pages_ids: list,
        sync_source: str,
        last_modified_source: str
    ):
    """
    Bulk sync: Update existing tasks from Notion.
    Only updates tasks that already exist in the database.

    CRITICAL: pages_ids must contain Notion UUIDs WITH DASHES
    """
    logger.debug(f"update_pages_by_ids: Updating tasks for user_id={user_id} from {len(pages_ids)} Notion pages")

    updated_pages = []

    # For each Notion page, check if task exists in DB and update it
    for page_id in pages_ids:
        logger.debug(f"Checking for update: page_id={page_id}, user_id={user_id}")

        # Query: find task by notion_page_id AND user_id
        stmt = select(UserNotionTask).where(
            UserNotionTask.notion_page_id == page_id,  # Search WITH dashes
            UserNotionTask.user_id == user_id  # Filter by user
        )
        result = await db.execute(statement=stmt)
        task = result.scalar_one_or_none()

        if not task:
            # Task doesn't exist for this user - skip (will be created by add_tasks_to_db)
            logger.debug(f"Task not found for update (page_id={page_id}, user_id={user_id}); skipping")
            continue

        # Fetch latest data from Notion
        try:
            page = await notion.pages.retrieve(page_id=page_id)
            notion_page = NotionTask.from_notion(page)
        except Exception as e:
            logger.error(f"Failed to fetch page from Notion (page_id={page_id}): {e}")
            continue

        # Task exists: UPDATE it
        logger.info(f"Updating task (id={task.id}, notion_page_id={page_id}, title='{notion_page.title}')")

        await update_task(
            db=db,
            task=task,
            title=notion_page.title,
            notion_url=notion_page.notion_page_url,
            description=notion_page.description,
            start_date=to_utc_datetime(notion_page.start_date),
            end_date=to_utc_datetime(notion_page.end_date),
            status=notion_page.status,
            select_option=notion_page.select_option,
            done=notion_page.done,
            priority=notion_page.priority,
            sync_source=sync_source,
            last_modified_source=last_modified_source
        )

        updated_pages.append({
            "page_id": page_id,
            "task_id": task.id,
            "title": notion_page.title,
            "status": "updated"
        })

    logger.info(f"Updated {len(updated_pages)} existing tasks")
    return updated_pages

