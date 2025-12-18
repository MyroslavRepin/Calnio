# Todo: In one function get user where active_sync=True
from server.app.core.config import settings
from server.db.deps import async_get_db_cm
from server.db.models import User
from sqlalchemy import select
from server.app.core.logging_config import logger
from server.deps.scheduler_client import get_scheduler
from server.services.sync.sync_service import SyncService
from server.services.sync.utils.caldav_orm import CalDavORM



async def sync_remote_to_local_for_all_users():
    async with async_get_db_cm() as db:
        stmt = select(User).where(
            User.active_sync.is_(True),
            User.icloud_email.isnot(None),
            User.app_specific_password.isnot(None)
        )
        result = await db.execute(stmt)
        users = result.scalars().all()

    try:
        scheduler = get_scheduler()
    except Exception as e:
        logger.error(f"Error getting scheduler: {e}")
        return

    async def sync_user_job(user_id: int):
        """Job function for syncing a single user's calendar"""
        try:
            logger.info(f"Starting sync for user {user_id}")
            async with async_get_db_cm() as db_inner:
                user = await db_inner.get(User, user_id)
                if not user:
                    logger.warning(f"User {user_id} not found")
                    return

                orm = SyncService(user_id=user.id)
                caldav_orm = CalDavORM(user_id=user.id)
                await caldav_orm.authenticate()
                calendar = await caldav_orm.Calendar.get_by_name(user.caldav_calendar_name)

                if not calendar:
                    logger.error(f"Calendar '{user.caldav_calendar_name}' not found for user {user_id}")
                    return

                logger.info(f"Found calendar: {calendar.name} for user {user_id}")
                async with async_get_db_cm() as db2:
                    await orm.sync_caldav_to_db(db=db2, calendar=calendar)
                logger.info(f"Completed sync for user {user_id}")
        except Exception as e:
            logger.error(f"Error syncing user {user_id}: {e}", exc_info=True)

    # Run initial sync for all users immediately
    logger.info(f"Running initial sync for {len(users)} user(s)")
    for user in users:
        await sync_user_job(user.id)

    # Adding separate jobs for each user with interval trigger
    default_sync_interval = settings.default_sync_interval_seconds

    for user in users:
        if user.sync_interval:
            sync_interval = user.sync_interval
        else:
            sync_interval = default_sync_interval

        scheduler.add_job(
            sync_user_job,
            'interval',
            seconds=sync_interval,
            args=(user.id,),
            id=f"sync_user_{user.id}",
            replace_existing=True
        )
        logger.info(f"Scheduled interval sync job for user {user.id} (every {sync_interval}s)")

    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started successfully")
