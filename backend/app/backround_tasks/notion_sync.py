from backend.app.core.config import settings
from backend.app.models.tasks import UserNotionTask
from backend.app.schemas.notion_pages import NotionTask
from notion_client import AsyncClient
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio
from datetime import datetime
import uuid

from backend.app.models.users import User
from backend.app.schemas.users import UserCreate
from backend.app.tools.notion.utils import get_all_ids

# Set up debug logging
def setup_debug_logging():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

setup_debug_logging()

async def get_all_ids(notion):
    logging.debug("Entering get_all_ids")
    from backend.app.crud.tasks import async_create_task
    result = await notion.search()
    logging.debug(f"Notion search result: {result}")
    database_ids = [
        obj["id"]
        for obj in result["results"]
        if obj["object"] == "database"
    ]
    logging.debug(f"Found database_ids: {database_ids}")
    page_ids = []
    for db_id in database_ids:
        logging.debug(f"Querying database_id: {db_id}")
        query_result = await notion.databases.query(database_id=db_id)
        logging.debug(f"Query result for {db_id}: {query_result}")
        for row in query_result.get("results", []):
            if row["object"] == "page":
                page_id = row["id"]
                try:
                    page_test = await notion.pages.retrieve(page_id=page_id)
                    if page_test.get("url"):
                        page_ids.append(page_id)
                        logging.debug(f"Added page_id: {page_id}")
                except Exception as e:
                    logging.warning(f"Page {page_id} could not be retrieved: {e}")
    logging.debug(f"Returning page_ids: {page_ids}")
    return page_ids

async def async_create_task(
    db: AsyncSession,
    user_id: int,
    title: str,
    notion_page_id: str,
    notion_url: str,
    description: str | None = None,
    task_date: str | None = None,  # приходит строкой из формы или NotionTask
    status: str | None = None,
    done: bool = False,
    priority: str | None = None,
    select_option: str | None = None,
) -> UserNotionTask:
    logging.debug(f"Entering async_create_task for user_id={user_id}, notion_page_id={notion_page_id}")
    stmt = select(UserNotionTask).where(
        UserNotionTask.user_id == user_id,
        UserNotionTask.notion_page_id == notion_page_id
    )
    result = await db.execute(stmt)
    existing_task = result.scalar_one_or_none()
    task_date_dt = None
    if task_date:
        try:
            task_date_dt = datetime.fromisoformat(task_date)
        except Exception as e:
            logging.warning(f"Failed to parse task_date '{task_date}': {e}")
    if existing_task:
        logging.debug(f"Updating existing task {existing_task.id}")
        existing_task.title = title
        existing_task.notion_url = notion_url
        existing_task.description = description
        existing_task.task_date = task_date_dt
        existing_task.status = status
        existing_task.done = done
        existing_task.priority = priority
        existing_task.select_option = select_option
        # Always set default values for required fields
        existing_task.sync_source = "notion"
        existing_task.last_synced_at = datetime.utcnow()
        existing_task.caldav_uid = "not supported yet"
        existing_task.has_conflict = False
        existing_task.last_modified_source = "notion"
        await db.commit()
        await db.refresh(existing_task)
        logging.debug(f"Updated task {existing_task.id}")
        return existing_task
    new_task = UserNotionTask(
        id=str(uuid.uuid4()),
        user_id=user_id,
        notion_page_id=notion_page_id,
        notion_url=notion_url,
        title=title,
        description=description,
        task_date=task_date_dt,
        status=status,
        done=done,
        priority=priority,
        select_option=select_option,
        # Always set default values for required fields
        sync_source="notion",
        last_synced_at=datetime.utcnow(),
        caldav_uid="not supported yet",
        has_conflict=False,
        last_modified_source="notion"
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    logging.debug(f"Created new task {new_task.id}")
    return new_task

async def add_tasks_to_db(db: AsyncSession, notion: AsyncClient, user_id):
    logging.debug(f"Entering add_tasks_to_db for user_id={user_id}")
    all_ids = await get_all_ids(notion=notion)
    logging.debug(f"All Notion page IDs: {all_ids}")
    added_pages = []
    for page_info in all_ids:
        page_id = page_info
        logging.debug(f"Processing page_id: {page_id}")
        page = await notion.pages.retrieve(page_id=page_id)
        logging.debug(f"Retrieved page: {page}")
        notion_page = NotionTask.from_notion(page)
        logging.debug(f"Parsed NotionTask: {notion_page}")
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
        logging.debug(f"Added page to result: {added_pages[-1]}")
    logging.debug(f"Returning from add_tasks_to_db: {added_pages}")
    return added_pages

async def delete_pages_by_ids(db: AsyncSession, notion: AsyncClient, user_id: int, pages_ids: list):
    logging.debug(f"Entering delete_pages_by_ids for user_id={user_id}")
    stmt = select(UserNotionTask).where(UserNotionTask.user_id == user_id)
    result = await db.execute(stmt)
    tasks = result.scalars().all()
    pages_ids_db = [task.notion_page_id for task in tasks]
    pages_to_delete = list(set(pages_ids_db) - set(pages_ids))
    logging.debug(f"Pages to delete: {pages_to_delete}")
    for page_id in pages_to_delete:
        stmt = select(UserNotionTask).where(
            UserNotionTask.notion_page_id == page_id,
            UserNotionTask.user_id == user_id
        )
        result = await db.execute(stmt)
        task = result.scalar()
        if task:
            await db.delete(task)
            logging.info(f"Deleted task with notion_page_id: {page_id}")
    await db.commit()
    logging.debug(f"Deleted pages committed: {pages_to_delete}")
    return {"deleted_pages": pages_to_delete}

async def update_task(db: AsyncSession, user_id, data: dict, task: UserNotionTask):
    logging.debug(f"Entering update_task for user_id={user_id}, task_id={getattr(task, 'id', None)}")
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
        logging.debug(f"Updated task {task.id}")
    else:
        logging.warning("Task does not exist")
        return "Task does not exist"
    return task

async def update_pages_by_ids(db: AsyncSession, notion: AsyncClient, user_id: int, pages_ids: list):
    logging.debug(f"Entering update_pages_by_ids for user_id={user_id}")
    stmt = select(UserNotionTask).where(UserNotionTask.user_id == user_id)
    result = await db.execute(stmt)
    tasks = result.scalars().all()
    all_ids = await get_all_ids(notion=notion)
    logging.debug(f"All Notion page IDs for update: {all_ids}")
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
        logging.debug(f"Updated page_id: {page_id}")

async def notion_sync_background(db, notion, user_id):
    added = await add_tasks_to_db(db, notion, user_id)
    current_notion_pages = await get_all_ids(notion)
    deleted = await delete_pages_by_ids(db, notion, user_id, current_notion_pages)
    updated = await update_pages_by_ids(db, notion, user_id, current_notion_pages)
    return {
        "added": added,
        "deleted": deleted,
        "updated": updated
    }
