from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.deps import async_get_db_cm
from server.db.models import UserNotionTask, User
from server.db.models.caldav_events import CalDavEvent
from server.services.caldav.caldav_orm import CalDavORM
from server.app.core.logging_config import logger
from server.utils.utils import extract_uid
import aiohttp
from icalendar import Calendar
from zoneinfo import ZoneInfo
from datetime import datetime
from typing import List, Dict, Any

class CaldavEventsRepository:

    async def sync_user_events(self):
        user_id = 7
        orm = CalDavORM(user_id=user_id)
        await orm.authenticate()
        calendar = await orm.Calendar.get_by_name("Personal")


        async with async_get_db_cm() as db:
            stmt = (
                select(UserNotionTask)
                .where(
                    UserNotionTask.user_id == user_id,
                    UserNotionTask.start_date.is_not(None),
                    UserNotionTask.end_date.is_not(None)
                )
            )
            result = await db.execute(stmt)
            tasks = result.scalars().all()

        for task in tasks:
            logger.info(f"Syncing task '{task.title}' for user ID: {user_id}")

            try:
                task_uid = getattr(task, "uid", str(task.id))

                # Проверяем, есть ли уже событие с таким user_id + caldav_uid
                stmt = select(CalDavEvent).where(
                    CalDavEvent.user_id == user_id,
                    CalDavEvent.caldav_uid == task_uid
                )
                result = await db.execute(stmt)
                existing_event = result.scalars().first()

                if existing_event:
                    logger.info(f"Task '{task.title}' already exists, skipping insert")
                    continue

                new_event = CalDavEvent(
                    user_id=user_id,
                    caldav_uid=task_uid,
                    title=task.title,
                    description=task.description,
                    start_time=task.start_date,
                    end_time=task.end_date,
                    sync_source="caldav"
                )
                db.add(new_event)

                logger.info(f"Task '{task.title}' added for sync")

            except Exception as e:
                logger.error(f"Failed to sync task '{task.title}': {e}")
                await db.rollback()

        try:
            await db.commit()
            logger.info("All tasks synced successfully")
        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")
            await db.rollback()

    async def sync_caldav_to_db(self, user_id: int, calendar_name: str):
        orm = CalDavORM(user_id=user_id)
        await orm.authenticate()
        calendar = await orm.Calendar.get_by_name(calendar_name)

        events = await orm.Event.all(calendar_uid=extract_uid(calendar.id))

        for event in events:
            logger.info(f"Syncing event '{event.title}' for user ID: {user_id}")

            try:
                async with async_get_db_cm() as db:
                    # Проверяем, есть ли уже запись
                    stmt = select(CalDavEvent).where(
                        CalDavEvent.user_id == user_id,
                        CalDavEvent.caldav_uid == event.uid
                    )
                    result = await db.execute(stmt)
                    existing_event = result.scalars().first()

                    if existing_event:
                        logger.info(f"Event '{event.title}' already exists, skipping")
                        continue

                    new_event = CalDavEvent(
                        user_id=user_id,
                        caldav_uid=event.uid,
                        title=event.title,
                        description=event.description,
                        start_time=event.start,
                        end_time=event.end,
                        sync_source="caldav"
                    )
                    db.add(new_event)

            except Exception as e:
                logger.error(f"Failed to process event '{event.title}': {e}")
                await db.rollback()

        try:
            await db.commit()
            logger.info("CalDAV events synced successfully")
        except Exception as e:
            logger.error(f"Failed to commit CalDAV sync: {e}")
            await db.rollback()

    async def fetch_ical_event(self, user_id, calendar, event_url, db: AsyncSession):
        """
        Fetches the event in iCalendar format from the CalDAV server.
        
        Args:
            user_id: ID of the user to authenticate with
            calendar: Calendar object containing authentication details
            event_url: URL of the event to fetch
            
        Returns:
            str: iCalendar data for the event, or None if fetch fails
        """
        async with aiohttp.ClientSession() as session:
            stmt = select(User.icloud_email, User.app_specific_password).where(User.id == user_id)
            result = await db.execute(stmt)
            user_credentials = result.one_or_none()
            if not user_credentials:
                logger.error(f"No user credentials found for user ID: {user_id}")
                return None
            else:
                icloud_email = str(user_credentials.icloud_email)
                app_specific_password = str(user_credentials.app_specific_password)
            try:
                async with session.get(
                        str(event_url),
                        auth=aiohttp.BasicAuth(icloud_email, app_specific_password),
                ) as resp:
                    ics_data = await resp.text()
                    # logger.debug(ics_data)
                    return ics_data
            except Exception as e:
                logger.error(f"Failed to fetch event as ical: {e}")
                return None

    async def parse_ical_full(self, ics_data: str) -> List[Dict[str, Any]]:
        events = []
        cal = Calendar.from_ical(ics_data)

        for component in cal.walk():
            if component.name != "VEVENT":
                continue

            dtstart = component.get("DTSTART").dt
            dtend = component.get("DTEND").dt
            tzinfo = None
            if hasattr(dtstart, "tzinfo") and dtstart.tzinfo:
                tzinfo = dtstart.tzinfo
            elif "TZID" in component.get("DTSTART").params:
                tzinfo = ZoneInfo(component.get("DTSTART").params["TZID"])

            event_data = {
                "uid": str(component.get("UID")),
                "title": str(component.get("SUMMARY", "")),
                "description": str(component.get("DESCRIPTION", "")),
                "created": component.get("CREATED").dt if component.get("CREATED") else None,
                "last_modified": component.get("LAST-MODIFIED").dt if component.get("LAST-MODIFIED") else None,
                "start": dtstart if isinstance(dtstart, datetime) else None,
                "end": dtend if isinstance(dtend, datetime) else None,
                "sequence": int(component.get("SEQUENCE", 0)),
                "url": str(component.get("URL")) if component.get("URL") else None,
                "timezone": str(tzinfo) if tzinfo else None,
                "raw_component": component,  # на всякий случай, если надо будет что-то ещё
            }

            events.append(event_data)

        return events