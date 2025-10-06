from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from server.db.database import async_engine, Base
import asyncio
from server.app.core.logging_config import logger


async def async_create_all_tables():
    """Create all tables in the database asynchronously."""
    try:
        logger.info("🔧 Creating all tables (async)...")
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ All tables created successfully (async)")
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")


# For backward compatibility, keep the old function name as an alias
async_create_tables = async_create_all_tables


async def async_check_connection():
    """Асинхронная проверка подключения к БД"""
    try:
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            logger.info(f"✅ Async connection successful! Query result: {result.scalar()}")
    except SQLAlchemyError as e:
        logger.error(f"❌ Connection error (async): {e}")


if __name__ == "__main__":
    asyncio.run(async_create_all_tables())

# Todo: Move and config here files create_missing_tables.py, recreate_tables.py (tools/)