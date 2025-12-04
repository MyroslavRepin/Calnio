import asyncio
import json

import asyncpg

from server.db.database import engine
from sqlalchemy import select
from server.app.core.logging_config import logger
from server.app.core.config import settings
from server.db.deps import async_get_db_cm
from server.db.models import User, UserNotionTask
from server.db.redis_client import get_redis
from server.services.notion_syncing.notion_sync import db_to_notion_sync
from server.utils.redis.utils import save_webhook_data


async def listen_to_postgres(channel='my_channel'):
    conn = await asyncpg.connect("postgresql://postgres:TxgyMUDOCAXOedvxSoXVsteYpvuprNnt@turntable.proxy.rlwy.net:25860/railway")
    await conn.add_listener(channel, handle_notification)
    logger.info(f"Listening to Postgres channel: {channel}")
    while True:
        await asyncio.sleep(3600)  # держим соединение открытым


async def handle_notification(conn, pid, channel, payload):
    data = json.loads(payload)
    page_id = data.get("id")

    async with async_get_db_cm() as db:
        stmt = select(UserNotionTask).where(UserNotionTask.id == page_id)
        result = await db.execute(stmt)
        task = result.scalars().first()

        if not task:
            logger.warning(f"No task found for id={page_id}")
            return

        # if changes came from background sync, skip syncing
        if task.sync_source in ("notion", "background"):
            logger.debug(f"Skipping db_to_notion_sync for task_id={task.id}, sync_source={task.sync_source}")
            return

        user_id = task.user_id

    operation = data.get("operation")
    redis_client = await get_redis()
    redis_data = {"page_id": page_id, "operation": operation, "user_id": user_id}

    await save_webhook_data(user_id, redis_data, redis=redis_client)
    await db_to_notion_sync(db=db, user_id=user_id)

    logger.debug(f"Recieved Postgres notification payload: {redis_data}")