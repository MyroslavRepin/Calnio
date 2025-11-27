import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from server.db.models import UserNotionTask
from server.db.models.enums import SyncStatus
from server.db.repositories.caldav_events import CaldavEventsRepository
from server.services.caldav.utils.caldav_orm import CalDavORM
from server.utils.utils import extract_uid, ensure_datetime_with_tz
from server.db.repositories.notion_tasks import NotionTaskRepository
from server.db.models.caldav_events import CalDavEvent
from server.app.core.logging_config import logger
from sqlalchemy import select


class SyncService:
    def __init__(self, user_id):
        self.user_id = user_id
        self.repo = CaldavEventsRepository()
        self.caldav_orm = CalDavORM(user_id=user_id)
        self.notion_orm = NotionTaskRepository()

    async def sync_db_to_caldav(self):
        """
        Синхронизация задач из базы данных на CalDAV.
        Пропускаем задачи без полного времени начала и окончания.
        """
        await self.caldav_orm.authenticate()

        calendar = await self.caldav_orm.Calendar.get_by_name("Personal")

        if not calendar:
            logger.error(f"Calendar: {calendar.title} not found")
            return

        calendar_uid = extract_uid(calendar.url)
        logger.debug(f"Calendar UID: {calendar_uid}")

        # Getting all tasks from UserNotionTasks
        db_events = await self.notion_orm.get_all_tasks(user_id=self.user_id)

        # Fixme: The problem is that notion_tasks table does not have a proper caldav UID
        for task in db_events:
            start = ensure_datetime_with_tz(task.start_date)
            end = ensure_datetime_with_tz(task.end_date)

            # Skip tasks without start or end date
            if start is None or end is None:
                logger.warning(f"Task '{task.title}' skipped: start or end date is missing")
                continue

            event_uid = extract_uid(str(task.id))
            logger.debug(f"Event UID: {event_uid}")

            exist = await self.caldav_orm.Event.get(calendar=calendar, event_uid=event_uid)
            if exist:
                logger.info(f"Event exist: {exist}")

            else:
                logger.info(f"Task with title: {task.title} does not exist in CalDav")

    async def sync_caldav_to_db(self, user_id: int, calendar, db: AsyncSession):
        """
        This function is only syncing events from CalDAV to caldav_events. It inlcudes:
        - Updating already existing events in caldav_events (but update only if last_modified is more fresh from remote)
        - Creating new events in caldav_events if they do not exist
        - Marking events as deleted=True in caldav_events if they are deleted in CalDAV
        """
        # await self.caldav_orm.authenticate()

        # CalDav events
        events = calendar.events()

        # deleted_events = await self.caldav_orm.Event.get_deleted_events(calendar=calendar, db=db, user_id=user_id)

        """
        Roadmap:
            1. Delete events from caldav_events if they are deleted in CalDAV
        """
        logger.info(f"Events: {events}")
        for event in events:

            # CalDav constants
            event_uid = extract_uid(event.url)
            ical_url = str(event.url).strip()

            # Get RAW event data from CalDAV
            event_raw = await self.repo.fetch_ical_event(
                user_id=user_id,
                calendar=calendar,
                event_url=ical_url,
                db=db
            )
            parsed_parsed_ical_dataata = await self.repo.parse_ical_full(event_raw)
            title = parsed_parsed_ical_dataata[0]["title"]

            # Check if event exists in both CalDAV and Notion
            stmt_caldav = select(CalDavEvent).where(
                CalDavEvent.user_id == user_id,
                CalDavEvent.caldav_uid == event_uid
            )
            existing_caldav_event = (await db.execute(stmt_caldav)).scalars().first()

            stmt_notion = select(UserNotionTask).where(
                UserNotionTask.user_id == user_id,
                UserNotionTask.caldav_id == event_uid
            )
            existing_notion_event = (await db.execute(stmt_notion)).scalars().first()

            new_notion_id = str(uuid.uuid4())


            # Determine last modified date
            raw_last_modified = parsed_parsed_ical_dataata[0].get("last_modified") or parsed_parsed_ical_dataata[0].get("created")
            last_modified_caldav = ensure_datetime_with_tz(raw_last_modified)

            notion_updated_at = None
            if existing_notion_event:
                notion_updated_at = ensure_datetime_with_tz(existing_notion_event.updated_at)
                if notion_updated_at is None:
                    notion_updated_at = ensure_datetime_with_tz(existing_notion_event.created_at)

            logger.info(f"Event title: {title}")
            logger.info(f"Last modified date: {last_modified_caldav}")



    async def sync_user_events(self):
        await self.caldav_orm.authenticate()

        calendar = await self.caldav_orm.Calendar.get_by_name("Personal")
        caldav_events = await self.caldav_orm.Event.all(calendar_uid=extract_uid(calendar.uid))

        db_events = await self.notion_orm.get_all_tasks(user_id=self.user_id)


        # 1. Sync all events from caldav to db
        await self.repo.sync_caldav_to_db(user_id=self.user_id, calendar_name="Personal")

        # 2. Sync all events from db to caldav
        await self.sync_db_to_caldav()
