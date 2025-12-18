from server.db.deps import async_get_db_cm
from server.db.models.users import User
from server.db.models.calendars import Calendar
from sqlalchemy import select
from server.app.core.logging_config import logger
from server.services.sync.utils.caldav_orm import CalDavORM
from server.utils.utils import extract_uid


async def sync_user_calendars():
    async with async_get_db_cm() as db:
        stmt = (
            select(User)
            .where(
                User.active_sync.is_(True),
                User.icloud_email.is_not(None),
                User.app_specific_password.is_not(None)
            )
        )
        result = await db.execute(stmt)
        users = result.scalars().all()

        for user in users:
            logger.info(f"Syncing calendars for user: {user.username}")

            orm = CalDavORM(user_id=user.id)
            await orm.authenticate()

            calendars = await orm.Calendar.all()

            for cal in calendars:
                stmt = select(Calendar).where(
                        Calendar.user_id == user.id,
                        Calendar.uid == extract_uid(str(cal["url"]))
                    )
                existing = await db.execute(stmt)
                existing_calendar = existing.scalar_one_or_none()

                raw_uid = cal.get("uid") or cal.get("event_uid")
                if not raw_uid:
                    logger.error(f"Calendar dict has no uid keys: {cal.keys()}")
                    return  # или continue, если это в цикле

                uid = extract_uid(str(raw_uid))

                if not existing_calendar:
                    logger.info("Adding new calendar")
                    new_calendar = Calendar(
                        user_id=user.id,
                        uid=uid,
                        name=cal.get("name"),
                        url=str(cal.get("url")),
                        color=None
                    )
                    db.add(new_calendar)
                else:
                    logger.info("Updating existing calendar")
                    existing_calendar.name = cal.get("name")
                    existing_calendar.url = str(cal.get("url"))
                    existing_calendar.color = None

            await db.commit()
