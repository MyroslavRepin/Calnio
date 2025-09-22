from backend.app.core.config import settings
from backend.app.models.tasks import UserNotionTask
from backend.app.schemas.notion_pages import NotionTask
from backend.app.core.config import settings

from notion_client import AsyncClient
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


async def get_all_ids(notion):
    from backend.app.crud.tasks import async_create_task

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
