from backend.app.models.users import User
from backend.app.models.notion_integration import UserNotionIntegration
from backend.app.models.tasks import UserNotionTask
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from backend.app.core.config import settings

from backend.app.db.database import engine, async_engine, Base
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
