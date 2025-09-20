from backend.app.crud.tasks import async_create_task
from backend.app.core.config import settings
from backend.app.models.tasks import UserNotionTask
from backend.app.schemas.notion_pages import NotionTask
from backend.app.core.config import settings

from notion_client import AsyncClient
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


async def get_all_ids_clean(notion):
    result = await notion.search()
    database_ids = [obj["id"]
                    for obj in result["results"] if obj["object"] == "database"]

    all_pages_status = []
    for db_id in database_ids:
        query_result = await notion.databases.query(database_id=db_id)
        for row in query_result.get("results", []):
            if row["object"] == "page":
                page_id = row["id"]
                try:
                    page_test = await notion.pages.retrieve(page_id=page_id)
                    page_url = page_test.get("url")
                    if page_url:
                        all_pages_status.append(
                            {"id": page_id, "status": "ok", "url": page_url}
                        )
                    else:
                        all_pages_status.append(
                            {"id": page_id, "status": "failed",
                                "error": "No URL returned"}
                        )
                except Exception as e:
                    logging.warning(
                        f"Page {page_id} could not be retrieved: {e}")
                    all_pages_status.append(
                        {"id": page_id, "status": "failed", "error": str(e)}
                    )

    return all_pages_status


async def get_all_ids(notion):
    result = await notion.search()
    database_ids = [
        obj["id"]
        for obj in result["results"]
        if obj["object"] == "database"
    ]

    page_ids = []
    for db_id in database_ids:
        query_result = await notion.databases.query(database_id=db_id)
        for row in query_result.get("results", []):
            if row["object"] == "page":
                page_id = row["id"]
                try:
                    page_test = await notion.pages.retrieve(page_id=page_id)
                    if page_test.get("url"):
                        page_ids.append(page_id)
                except Exception as e:
                    logging.warning(
                        f"Page {page_id} could not be retrieved: {e}")

    return page_ids


async def add_tasks_to_bd(db: AsyncSession, notion: AsyncClient, user_id):
    all_ids = await get_all_ids(notion=notion)
    added_pages = []

    for page_info in all_ids:
        page_id = page_info
        print(page_id)

        page = await notion.pages.retrieve(page_id=page_id)
        notion_page = NotionTask.from_notion(page)

        await async_create_task(
            db=db,
            user_id=user_id,
            notion_url=notion_page.notion_page_url,
            notion_page_id=page_id,
            title=notion_page.title,
            description=notion_page.description,
            task_date=notion_page.task_date,
            status=notion_page.status,
            select_option=notion_page.select_option,
            done=notion_page.done,
            priority=notion_page.priority
        )

        added_pages.append({
            "page_id": page_id,
            "title": notion_page.title,
            "status": "added"
        })

    return added_pages


async def delete_pages_by_ids(db: AsyncSession, notion: AsyncClient, user_id: int, pages_ids: list):
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


async def update_task(db: AsyncSession, user_id, data: dict, task: UserNotionTask):
    if task:
        task.title = data["title"]
        task.description = data["description"]
        task.task_date = data["task_date"]
        task.status = data["status"]
        task.select_option = data["select_option"]
        task.done = data["done"]
        task.priority = data["priority"]
        db.add(task)
        db.commit
    else:
        return "Task does not exist"
    return task


async def update_pages_by_ids(db: AsyncSession, notion: AsyncClient, user_id: int, pages_ids: list):
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

        data = {
            "notion_page_id": notion_page.notion_page_id,
            "notion_url": notion_page.notion_page_url,
            "title": notion_page.title,
            "description": notion_page.description,
            "task_date": notion_page.task_date,
            "status": notion_page.status,
            "select_option": notion_page.select_option,
            "done": notion_page.done,
            "priority": notion_page.priority
        }

        await update_task(db=db, user_id=user_id, data=data, task=task)
