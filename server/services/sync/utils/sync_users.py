from server.db.deps import async_get_db_cm
from server.services.sync.sync_manager import SyncService
from server.db.models import User
from sqlalchemy import select
from server.app.core.logging_config import logger


DEFAULT_CALDAV_CALENDAR_NAME = "Personal"


async def sync_caldav_to_db_for_all_users() -> None:
    """Sync CalDAV data to DB for all *eligible* superusers.

    Eligibility:
    - user.active_sync is True
    - user has iCloud email + app-specific password configured

    Notes:
    - Designed to be executed by APScheduler/background tasks.
    - Failures for one user are logged and won't abort the whole run.
    """

    async with async_get_db_cm() as db:
        stmt = (
            select(User)
            .where(
                User.active_sync.is_(True),
                User.icloud_email.is_not(None),
                User.app_specific_password.is_not(None),
            )
        )
        result = await db.execute(stmt)
        users = result.scalars().all()

        if not users:
            logger.info("No eligible superusers found for CalDAV sync")
            return

        logger.info(f"Starting CalDAV sync for {len(users)} eligible superuser(s)")

        for user in users:
            try:
                logger.info(
                    f"Starting CalDAV sync for user_id={user.id} username={user.username}"
                )
                sync_service = SyncService(user_id=user.id)
                await sync_service.sync_caldav_to_db(
                    user_id=user.id,
                    calendar_name=DEFAULT_CALDAV_CALENDAR_NAME,
                    db=db,
                )
            except Exception:
                logger.exception(
                    f"CalDAV sync failed for user_id={user.id} username={user.username}"
                )

        logger.info("CalDAV sync job completed")
