# Todo: In one function get user where active_sync=True
import asyncio

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
        """Job function для одного пользователя"""
        async with async_get_db_cm() as db_inner:
            user = await db_inner.get(User, user_id)
            if not user:
                return
            orm = SyncService(user_id=user.id)
            caldav_orm = CalDavORM(user_id=user.id)
            await caldav_orm.authenticate()
            calendar = await caldav_orm.Calendar.get_by_name(user.caldav_calendar_name)
            async with async_get_db_cm() as db2:
                await orm.sync_caldav_to_db(db=db2, calendar=calendar)

    # Adding separate jobs for each user
    for user in users:
        scheduler.add_job(
            sync_user_job,
            args=(user.id,),
            id=f"sync_user_{user.id}",
            replace_existing=True
        )
        logger.info(f"Scheduled sync job for user {user.id}")
    scheduler.start()
    # try:
    #     asyncio.get_event_loop().run_forever()
    # except (KeyboardInterrupt, SystemExit):
    #     pass