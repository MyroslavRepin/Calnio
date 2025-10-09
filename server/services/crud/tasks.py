from server.app.core.logging_config import logger
from datetime import datetime, UTC
import uuid
from notion_client import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.models.tasks import UserNotionTask
from server.app.schemas.notion_pages import NotionTask
from server.utils.notion.utils import get_all_ids, to_utc_datetime, normalize_notion_id

# Part of CRUD just for one page
async def create_task(
    db: AsyncSession,
    user_id: int,
    title: str,
    notion_page_id: str,
    notion_url: str,
    #
    sync_source: str,
    last_synced_at: datetime = None,
    caldav_uid: str = None,
    has_conflict: bool = False,
    last_modified_source: str | None = None,
    #
    description: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    status: str | None = None,
    done: bool = False,
    priority: str | None = None,
    select_option: str | None = None
) -> UserNotionTask:
    # Normalize notion_page_id by removing dashes
    notion_page_id_normalized = normalize_notion_id(notion_page_id)

    logger.debug(f"Looking for existing task with notion_page_id: {notion_page_id_normalized}")

    # Check if task already exists by notion_page_id (which is unique)
    stmt = select(UserNotionTask).where(
        UserNotionTask.notion_page_id == notion_page_id_normalized
    )
    result = await db.execute(stmt)
    existing_task = result.scalar_one_or_none()

    # Convert start_date and end_date to datetime
    start_date_dt = to_utc_datetime(start_date)
    end_date_dt = to_utc_datetime(end_date)

    if existing_task:
        # Update existing task
        logger.info(f"Updating existing task: '{existing_task.title}' → '{title}' (id: {existing_task.id})")
        existing_task.title = title
        existing_task.notion_url = notion_url
        existing_task.description = description
        existing_task.start_date = start_date_dt
        existing_task.end_date = end_date_dt
        existing_task.status = status
        existing_task.done = done
        existing_task.priority = priority
        existing_task.select_option = select_option
        # Always set default values for required fields
        existing_task.sync_source = sync_source
        existing_task.last_synced_at = datetime.now(UTC)
        existing_task.caldav_uid = caldav_uid if caldav_uid else "not supported yet"
        existing_task.has_conflict = bool(has_conflict)
        existing_task.last_modified_source = last_modified_source
        await db.commit()
        await db.refresh(existing_task)
        logger.debug(f"Task updated in database")
        return existing_task

    # Create new task with normalized ID (no dashes) and UUID without dashes
    task_uuid = str(uuid.uuid4()).replace("-", "")
    logger.info(f"Creating NEW task: '{title}' (notion_page_id: {notion_page_id_normalized}, task_id: {task_uuid})")
    new_task = UserNotionTask(
        id=task_uuid,
        user_id=user_id,
        notion_page_id=notion_page_id_normalized,
        notion_url=notion_url,
        title=title,
        description=description,
        start_date=start_date_dt,
        end_date=end_date_dt,
        status=status,
        done=done,
        priority=priority,
        select_option=select_option,
        # Always set default values for required fields
        sync_source=sync_source,
        last_synced_at=datetime.now(UTC),
        caldav_uid=caldav_uid if caldav_uid else "not supported yet",
        has_conflict=bool(has_conflict),
        last_modified_source=last_modified_source
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    logger.debug(f"New task saved to database")
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
        # Always set default values for required fields
        task.sync_source = sync_source
        task.last_synced_at = datetime.now(UTC)
        task.caldav_uid = "not supported yet"
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
    Returns True if task was deleted, False if task was not found.
    """
    # Normalize page_id by removing dashes
    page_id_normalized = normalize_notion_id(page_id)

    stmt = select(UserNotionTask).where(
        UserNotionTask.notion_page_id == page_id_normalized,
        UserNotionTask.user_id == user_id
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()

    if task:
        logger.debug(f"Deleting task: {task.id} (notion_page_id: {page_id_normalized})")
        await db.delete(task)
        await db.commit()
        return True
    else:
        logger.debug(f"Task not found for deletion (notion_page_id: {page_id_normalized}, user_id: {user_id})")
        return False

# Syncing logics for each page separate (webhook)
async def sync_task_by_id(db: AsyncSession, notion: AsyncClient, user_id: int, page_id: str, event_type: str):
    page = await notion.pages.retrieve(page_id=page_id)
    notion_page = NotionTask.from_notion(page)
    start_date_utc = to_utc_datetime(notion_page.start_date)
    end_date_utc = to_utc_datetime(notion_page.end_date)

    if event_type == "page.created":
        logger.info(f"Creating task for new page: {page_id}")
        await create_task(
            db=db,
            user_id=user_id,
            title=notion_page.title,
            notion_url=notion_page.notion_page_url,
            sync_source="notion",
            notion_page_id=page_id,
            description=notion_page.description,
            start_date=start_date_utc,
            end_date=end_date_utc,
            status=notion_page.status,
            select_option=notion_page.select_option,
            done=notion_page.done,
            priority=notion_page.priority
        )
    else:
        logger.info(f"Received event '{event_type}' for page_id: {page_id}")

# Part of CRUD for all pages >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def add_tasks_to_db(
    db: AsyncSession,
    user_id: int,
    notion: AsyncClient,
    sync_source: str,
    last_synced_at: datetime = None,
    caldav_uid: str = None,
    has_conflict: bool = False,
    last_modified_source: str = "notion"
) -> list:
    all_ids = await get_all_ids(notion=notion)
    added_pages = []

    for page_info in all_ids:
        page_id = page_info
        logger.debug(f"Processing page_id: {page_id}")
        page = await notion.pages.retrieve(page_id=page_id)
        notion_page = NotionTask.from_notion(page)
        start_date_utc = to_utc_datetime(notion_page.start_date)
        end_date_utc = to_utc_datetime(notion_page.end_date)
        await create_task(
            db=db,
            user_id=user_id,
            notion_url=notion_page.notion_page_url,
            notion_page_id=page_id,
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
            caldav_uid=caldav_uid,
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
    # Получаем все задачи пользователя из БД
    stmt = select(UserNotionTask).where(UserNotionTask.user_id == user_id)
    result = await db.execute(stmt)
    tasks = result.scalars().all()

    # Собираем ID страниц из БД (already normalized, no dashes)
    pages_ids_db = [
        task.notion_page_id for task in tasks
    ]

    # Normalize page IDs from Notion (remove dashes)
    pages_ids_normalized = [normalize_notion_id(pid) for pid in pages_ids]

    # находим страницы, которые есть в БД, но НЕТ в Notion
    pages_to_delete = list(set(pages_ids_db) - set(pages_ids_normalized))

    # Удаляем устаревшие задачи
    for page_id in pages_to_delete:
        stmt = select(UserNotionTask).where(
            UserNotionTask.notion_page_id == page_id,
            UserNotionTask.user_id == user_id  # Добавляем проверку пользователя
        )
        result = await db.execute(stmt)
        task = result.scalar()
        if task:
            await db.delete(task)
            logger.info(f"Deleted task with notion_page_id: {page_id}")

    await db.commit()
    return {"deleted_pages": pages_to_delete}



async def update_pages_by_ids(
        db: AsyncSession,
        notion: AsyncClient,
        user_id: int,
        pages_ids: list,
        sync_source: str,
        last_modified_source: str
    ):
    # Getting all users pages from db
    stmt = select(UserNotionTask).where(UserNotionTask.user_id == user_id)
    result = await db.execute(stmt)
    tasks = result.scalars().all()

    # Getting pages info from all_ids
    all_ids = await get_all_ids(notion=notion)
    updated_pages = []

    for page_info in all_ids:
        page_id_raw = page_info
        page_id_normalized = normalize_notion_id(page_id_raw)

        logger.debug(f"Processing page update for: {page_id_normalized}")
        stmt = select(UserNotionTask).where(
            UserNotionTask.notion_page_id == page_id_normalized)
        result = await db.execute(statement=stmt)
        task = result.scalar_one_or_none()

        # Use raw page_id with dashes for Notion API
        page = await notion.pages.retrieve(page_id=page_id_raw)
        notion_page = NotionTask.from_notion(page)

        if task:
            # Update existing task
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
                "page_id": page_id_normalized,
                "title": notion_page.title,
                "status": "updated"
            })

    return updated_pages
