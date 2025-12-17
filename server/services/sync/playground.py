import os
import sys
import asyncio

from server.deps.scheduler_client import get_scheduler
from server.db.deps import async_get_db_cm

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from server.services.sync.utils.caldav_orm import CalDavORM
from server.services.sync.sync_service import SyncService
from server.app.core.logging_config import logger
from server.services.sync.main import sync_remote_to_local_for_all_users

from rich.traceback import install
install(show_locals=True)  # Add at startup



async def manual_sync():
    """Main entry point for manual testing."""
    orm = CalDavORM(user_id=3)
    sync_service = SyncService(user_id=3)
    await orm.authenticate()
    calendar_name = "Calnio"
    calendar = await orm.Calendar.get_by_name(calendar_name)
    if not calendar:
        logger.error(f"Calendar '{calendar_name}' not found!")
        return
    async with async_get_db_cm() as db:
        await sync_service.sync_caldav_to_db(db=db, calendar=calendar)

async def sync():
    orm = CalDavORM(user_id=3)
    sync_service = SyncService(user_id=3)
    await orm.authenticate()
    calendar_name = "Calnio"
    calendar = await orm.Calendar.get_by_name(calendar_name)
    if not calendar:
        logger.error(f"Calendar '{calendar_name}' not found!")
        return
    async with async_get_db_cm() as db:
        await sync_service.sync_caldav_to_db(calendar=calendar, db=db)


scheduler = get_scheduler()

async def scheduler_sync():
    logger.info("Starting Calnio sync scheduler")
    sync_interval = 30
    scheduler.add_job(
        sync,
        "interval",
        seconds=sync_interval,
        replace_existing=False,
        name="sync_user_events"
    )

    try:
        await sync()
        scheduler.start()
        logger.info(f"Scheduler started | interval={sync_interval}s")
        # This prevent from quitting the script
        try:
            while True:
                await asyncio.sleep(5)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Shutting down scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler stopped successfully")

    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()


async def main():
    """Main entry point that keeps the event loop running."""
    await sync_remote_to_local_for_all_users()

    logger.info("Scheduler is running. Press Ctrl+C to stop.")
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler...")
        scheduler = get_scheduler()
        scheduler.shutdown()
        logger.info("Scheduler stopped successfully")


if __name__ == "__main__":
    asyncio.run(main())
