import logging
from datetime import datetime
import uuid
from notion_client import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.tasks import UserNotionTask
from backend.app.schemas.notion_pages import NotionTask
from backend.app.tools.notion.utils import get_all_ids, to_utc_datetime


async def async_create_task(
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
    last_modified_source: str = "notion",
    #
    description: str | None = None,
    start_date: str | None = None,  # приходит строкой из формы или NotionTask
    end_date: str | None = None,    # new field
    status: str | None = None,
    done: bool = False,
    priority: str | None = None,
    select_option: str | None = None
) -> UserNotionTask:
    # Проверяем, есть ли уже задача с таким page_id
    stmt = select(UserNotionTask).where(
        UserNotionTask.user_id == user_id,
        UserNotionTask.notion_page_id == notion_page_id
    )
    result = await db.execute(stmt)
    existing_task = result.scalar_one_or_none()

    # Конвертируем start_date и end_date в datetime, если есть
    start_date_dt = to_utc_datetime(start_date)
    end_date_dt = to_utc_datetime(end_date)

    if existing_task:
        # обновляем существующую запись
        existing_task.title = title
        existing_task.notion_url = notion_url
        existing_task.description = description
        existing_task.start_date = start_date_dt
        existing_task.end_date = end_date_dt
        # Always set default values for required fields
        existing_task.sync_source = "notion"
        existing_task.last_synced_at = to_utc_datetime(datetime.utcnow())
        existing_task.caldav_uid = "not supported yet"
        existing_task.has_conflict = False
        existing_task.last_modified_source = "notion"
        await db.commit()
        await db.refresh(existing_task)
        return existing_task

    # создаём новую задачу
    new_task = UserNotionTask(
        id=str(uuid.uuid4()),
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
        # Always set default values for required fields
        sync_source="notion",
        last_synced_at=to_utc_datetime(datetime.utcnow()),
        caldav_uid="not supported yet",
        has_conflict=False,
        last_modified_source="notion"
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task


async def add_tasks_to_db(
    db: AsyncSession,
    user_id: int,
    notion: AsyncClient,
    sync_source: str = "notion",
    last_synced_at: datetime = None,
    caldav_uid: str = None,
    has_conflict: bool = False,
    last_modified_source: str = "notion"
) -> list:
    all_ids = await get_all_ids(notion=notion)
    added_pages = []

    for page_info in all_ids:
        page_id = page_info
        print(page_id)
        page = await notion.pages.retrieve(page_id=page_id)
        notion_page = NotionTask.from_notion(page)
        start_date_utc = to_utc_datetime(notion_page.start_date)
        end_date_utc = to_utc_datetime(notion_page.end_date)
        await async_create_task(
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

    # Собираем ID страниц из БД
    pages_ids_db = [
        task.notion_page_id for task in tasks
    ]

    # находим страницы, которые есть в БД, но НЕТ в Notion
    pages_to_delete = list(set(pages_ids_db) - set(pages_ids))

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
            logging.info(f"Deleted task with notion_page_id: {page_id}")

    await db.commit()
    return {"deleted_pages": pages_to_delete}


async def update_task(
        db: AsyncSession,
        user_id,
        data: dict,
        task: UserNotionTask):
    if task:
        task.title = data["title"]
        task.description = data["description"]
        task.start_date = to_utc_datetime(data["start_date"])
        task.end_date = to_utc_datetime(data["end_date"])
        task.status = data["status"]
        task.select_option = data["select_option"]
        task.done = data["done"]
        task.priority = data["priority"]
        db.add(task)
        await db.commit()
        await db.refresh(task)
    else:
        return "Task does not exist"
    return task


async def update_pages_by_ids(
        db: AsyncSession,
        notion: AsyncClient,
        user_id: int,
        pages_ids: list):
    # Getting all users pages from db
    stmt = select(UserNotionTask).where(UserNotionTask.user_id == user_id)
    result = await db.execute(stmt)
    tasks = result.scalars().all()

    # Getting pages info from all_ids
    all_ids = await get_all_ids(notion=notion)
    added_pages = []

    for page_info in all_ids:
        page_id = page_info
        logging.info("Pages in for loop")
        stmt = select(UserNotionTask).where(
            UserNotionTask.notion_page_id == page_id)
        result = await db.execute(statement=stmt)
        task = result.scalar()

        page = await notion.pages.retrieve(page_id=page_id)
        notion_page = NotionTask.from_notion(page)

        # Always change date to utc (to_utc_datetime)
        data = {
            "notion_page_id": notion_page.notion_page_id,
            "notion_url": notion_page.notion_page_url,
            "title": notion_page.title,
            "description": notion_page.description,
            "start_date": to_utc_datetime(notion_page.start_date),
            "end_date": to_utc_datetime(notion_page.end_date),
            "status": notion_page.status,
            "select_option": notion_page.select_option,
            "done": notion_page.done,
            "priority": notion_page.priority
        }

        await update_task(db=db, user_id=user_id, data=data, task=task)
