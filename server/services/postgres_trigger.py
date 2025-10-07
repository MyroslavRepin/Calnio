import asyncio
import json

import asyncpg

from server.db.database import engine
import select
from server.app.core.logging_config import logger
from server.app.core.config import settings

async def listen_to_postgres(channel='my_channel'):
    conn = await asyncpg.connect("postgresql://postgres:TxgyMUDOCAXOedvxSoXVsteYpvuprNnt@turntable.proxy.rlwy.net:25860/railway")
    await conn.add_listener(channel, handle_notification)
    logger.info(f"Listening to Postgres channel: {channel}")
    while True:
        await asyncio.sleep(3600)  # держим соединение открытым


def handle_notification(conn, pid, channel, payload):
    data = json.loads(payload)
    operation = data.get("operation")
    task_id = data.get("id")

    # компактно, в одну строку
    logger.debug(f"Operation={operation}, id={task_id}")