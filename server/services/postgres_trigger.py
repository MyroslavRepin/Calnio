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
        stmt = select(UserNotionTask.user_id).where(UserNotionTask.id == page_id)
        result = await db.execute(stmt)
        user_id = result.scalars().first()
    operation = data.get("operation")
    data = {
        "page_id": page_id,
        "operation": operation,
        "user_id": user_id,
    }
    redis_client = await get_redis()
    await save_webhook_data(user_id, data, redis=redis_client)
    logger.debug(f"Recieved Postgres notification payload: {data}")