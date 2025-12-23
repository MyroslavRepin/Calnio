from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from server.db.deps import async_get_db_cm
from server.db.models import User
from server.integrations.notion.notion_client import get_notion_client
from server.services.notion_syncing.notion_sync import notion_sync_background
from server.app.core.logging_config import logger
from server.services.caldav.user_calendars import sync_user_calendars
from server.services.sync.utils.sync_users import sync_caldav_to_db_for_all_users

# Scheduler singleton (kept module-local; expose via get_scheduler())
_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    """Return the process-wide scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
        register_jobs(_scheduler)
    return _scheduler


def register_jobs(scheduler: AsyncIOScheduler) -> None:
    """Register all APScheduler jobs (safe to call multiple times)."""

    # Calendar discovery/sync (existing behavior).
    scheduler.add_job(
        sync_user_calendars,
        "interval",
        minutes=5,
        id="sync_user_calendars",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )

    # Superuser-only: sync CalDAV events/items into DB for all eligible users.
    scheduler.add_job(
        sync_caldav_to_db_for_all_users,
        "interval",
        seconds=30,
        id="sync_caldav_to_db_for_all_users",
        max_instances=1,
        coalesce=True,
        replace_existing=False,
    )


async def sync_service():
    """
    Perform background synchronization for users with active sync enabled.

    This asynchronous function retrieves all users from the database, along with their related
    Notion integration data, and performs synchronization tasks for users who have enabled
    active sync. The synchronization utilizes the Notion API to update or fetch data relevant
    to the application's functionality. The function logs debug information to help
    track synchronization results and skipped users.

    Raises:
        Exception: An exception may be raised during database access, user processing, or
        Notion API interaction. Error handling should ensure proper function termination
        and logging of issues.
    """
    async with async_get_db_cm() as db:
        stmt = select(User).options(selectinload(User.notion_integration))
        result = await db.execute(stmt)
        users = result.scalars().all()
        for user in users:
            if user.active_sync == True:
                logger.debug(
                    f"Scheduler starts for: {user.username}!"
                )
                notion = get_notion_client(user.notion_integration.access_token)
                notion_sync_result = await notion_sync_background(db=db, notion=notion, user_id=user.id)
                logger.debug(f"notion_sync_result: {notion_sync_result}")
            else:
                logger.debug(
                    f"Scheduler skipped for: {user.username}!"
                )



def start_scheduler() -> None:
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()


def shutdown_scheduler(wait: bool = True) -> None:
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=wait)
