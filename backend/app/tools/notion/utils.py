from backend.app.crud.tasks import async_create_task
from backend.app.core.config import settings
from backend.app.schemas.notion_pages import NotionTask

import logging
from notion_client import AsyncClient
import logging
from backend.app.core.config import settings

from notion_client import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


async def get_all_ids(notion):
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


async def add_tasks_to_bd(db: AsyncSession, notion, user_id):
    all_ids = await get_all_ids(notion=notion)
    added_pages = []

    for page_info in all_ids:
        page_id = page_info["id"]
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
