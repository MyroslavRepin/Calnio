"""This file is for testing purposes, debugging and playground."""
import asyncio
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import select

from server.db.deps import async_get_db_cm
from server.db.models import User
from server.integrations.notion.notion_client import get_notion_client

async def get_raw_page():
    async with async_get_db_cm() as db:
        stmt = select(User).where(User.id == 7)
        result = await db.execute(stmt)
        user = result.scalars().first()

    notion = get_notion_client(user.notion_integration.access_token)
    page_id = "285a555872b480f8bcd2ed1612d48ec6"
    page = await notion.pages.retrieve(page_id=page_id)
    print(json.dumps(page, indent=4))

asyncio.run(get_raw_page())
