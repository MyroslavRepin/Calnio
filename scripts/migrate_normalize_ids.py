"""
Migration script to normalize all notion_page_id and task id values by removing dashes.
This ensures consistency with the new normalization logic.
"""
import asyncio
from sqlalchemy import text
from server.db.database import async_engine
from server.app.core.logging_config import logger

async def migrate_normalize_ids():
    """Normalize all notion_page_id and id values in notion_tasks table."""
    async with async_engine.begin() as conn:
        # First, check current state
        result = await conn.execute(
            text("SELECT COUNT(*) FROM notion_tasks WHERE notion_page_id LIKE '%-%'")
        )
        count_with_dashes = result.scalar()
        logger.info(f"Found {count_with_dashes} tasks with dashes in notion_page_id")

        if count_with_dashes == 0:
            logger.info("All notion_page_ids already normalized!")
            return

        # Update notion_page_id: remove all dashes
        logger.info("Normalizing notion_page_id values (removing dashes)...")
        await conn.execute(
            text("UPDATE notion_tasks SET notion_page_id = REPLACE(notion_page_id, '-', '')")
        )

        # Update task id: remove all dashes
        logger.info("Normalizing task id values (removing dashes)...")
        await conn.execute(
            text("UPDATE notion_tasks SET id = REPLACE(id, '-', '')")
        )

        # Verify the migration
        result = await conn.execute(
            text("SELECT COUNT(*) FROM notion_tasks WHERE notion_page_id LIKE '%-%'")
        )
        remaining_with_dashes = result.scalar()

        result = await conn.execute(
            text("SELECT COUNT(*) FROM notion_tasks WHERE id LIKE '%-%'")
        )
        ids_with_dashes = result.scalar()

        if remaining_with_dashes == 0 and ids_with_dashes == 0:
            logger.info(f"Successfully normalized {count_with_dashes} tasks!")
            logger.info("All notion_page_id and id values now have no dashes")
        else:
            logger.warning(f"Warning: {remaining_with_dashes} notion_page_ids and {ids_with_dashes} ids still have dashes")

async def show_sample_tasks():
    """Show sample tasks after migration."""
    async with async_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT id, notion_page_id, title FROM notion_tasks ORDER BY created_at DESC LIMIT 5")
        )
        logger.info("Sample tasks after migration:")
        logger.info("-" * 100)
        for row in result:
            logger.info(f"ID: {row[0][:32]} | notion_page_id: {row[1][:32]} | Title: {row[2]}")

if __name__ == "__main__":
    logger.info("Starting ID normalization migration...")
    logger.info("=" * 100)
    asyncio.run(migrate_normalize_ids())
    asyncio.run(show_sample_tasks())
    logger.info("=" * 100)
    logger.info("Migration complete!")
