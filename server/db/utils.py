from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from server.db.database import async_engine, Base
import asyncio
import logging


async def async_create_all_tables():
    """Create all tables in the database asynchronously."""
    try:
        print("Создаю все таблицы (async)...")
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Все таблицы созданы (async)")
    except Exception as e:
        logging.error(f"❌ Ошибка создания таблиц: {e}")


# For backward compatibility, keep the old function name as an alias
async_create_tables = async_create_all_tables


async def async_check_connection():
    """Асинхронная проверка подключения к БД"""
    try:
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ Async подключение успешно! Результат запроса:", result.scalar())
    except SQLAlchemyError as e:
        print("❌ Ошибка подключения (async):", e)


if __name__ == "__main__":
    asyncio.run(async_create_all_tables())

# Todo: Move and config here files create_missing_tables.py, recreate_tables.py (tools/)