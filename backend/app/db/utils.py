from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from backend.app.core.config import settings

from backend.app.db.database import engine, async_engine, Base
import asyncio


async def async_create_tables():
    """Create tables in async type"""
    print("Создаю таблицы (async)...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Таблицы созданы (async)")


async def async_check_connection():
    """Асинхронная проверка подключения к БД"""
    try:
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ Async подключение успешно! Результат запроса:", result.scalar())
    except SQLAlchemyError as e:
        print("❌ Ошибка подключения (async):", e)


if __name__ == "__main__":
    asyncio.run(async_create_tables())
