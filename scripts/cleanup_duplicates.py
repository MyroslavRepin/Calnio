"""
Cleanup script to:
1. Find and remove duplicate tasks (based on normalized notion_page_id)
2. Normalize all IDs by removing dashes
3. Ensure database consistency
"""
import asyncio
from sqlalchemy import text
from server.db.database import async_engine
from server.app.core.logging_config import logger

async def find_duplicates():
    """Find all duplicate tasks."""
    async with async_engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT 
                REPLACE(notion_page_id, '-', '') as normalized_id,
                COUNT(*) as count
            FROM notion_tasks
            GROUP BY REPLACE(notion_page_id, '-', '')
            HAVING COUNT(*) > 1
        """))

        duplicates = result.fetchall()
        logger.info(f"Found {len(duplicates)} sets of duplicate tasks")
        return duplicates

async def remove_duplicates():
    """Remove duplicate tasks, keeping only the most recent one."""
    async with async_engine.begin() as conn:
        # For each set of duplicates, keep only the most recent (by created_at)
        result = await conn.execute(text("""
            DELETE FROM notion_tasks
            WHERE id IN (
                SELECT id FROM (
                    SELECT 
                        id,
                        REPLACE(notion_page_id, '-', '') as normalized_id,
                        ROW_NUMBER() OVER (
                            PARTITION BY REPLACE(notion_page_id, '-', '') 
                            ORDER BY created_at DESC
                        ) as rn
                    FROM notion_tasks
                ) sub
                WHERE rn > 1
            )
            RETURNING id, notion_page_id, title
        """))

        deleted = result.fetchall()
        logger.info(f"Deleted {len(deleted)} duplicate tasks")
        for task in deleted:
            logger.debug(f"   Deleted: {task[1]} - {task[2]}")

        return len(deleted)

async def normalize_all_ids():
    """Normalize all notion_page_id and id values by removing dashes."""
    async with async_engine.begin() as conn:
        # Check current state
        result = await conn.execute(
            text("SELECT COUNT(*) FROM notion_tasks WHERE notion_page_id LIKE '%-%' OR id LIKE '%-%'")
        )
        count_with_dashes = result.scalar()

        if count_with_dashes == 0:
            logger.info("All IDs already normalized!")
            return

        logger.info(f"Normalizing {count_with_dashes} tasks with dashes...")

        # Update notion_page_id
        await conn.execute(
            text("UPDATE notion_tasks SET notion_page_id = REPLACE(notion_page_id, '-', '') WHERE notion_page_id LIKE '%-%'")
        )

        # Update task id
        await conn.execute(
            text("UPDATE notion_tasks SET id = REPLACE(id, '-', '') WHERE id LIKE '%-%'")
        )

        logger.info("All IDs normalized!")

async def show_final_state():
    """Show the final state of the database."""
    async with async_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT COUNT(*) FROM notion_tasks")
        )
        total = result.scalar()

        result = await conn.execute(
            text("SELECT id, notion_page_id, title FROM notion_tasks ORDER BY created_at DESC LIMIT 5")
        )

        logger.info(f"\nFinal state: {total} total tasks")
        logger.info("Recent tasks:")
        for row in result:
            logger.info(f"ID: {row[0][:32]} | notion_page_id: {row[1][:32]} | Title: {row[2]}")

async def main():
    logger.info("Starting database cleanup and normalization")
    # Step 1: Find duplicates
    duplicates = await find_duplicates()

    if duplicates:
        # Step 2: Remove duplicates (keep most recent)
        deleted_count = await remove_duplicates()
        logger.info(f"Removed {deleted_count} duplicate tasks")
    else:
        logger.info("No duplicates found")

    # Step 3: Normalize all IDs
    await normalize_all_ids()

    # Step 4: Show final state
    await show_final_state()

    logger.info("Cleanup complete!")

if __name__ == "__main__":
    asyncio.run(main())

