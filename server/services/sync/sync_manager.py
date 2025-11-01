import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from server.db.deps import async_get_db_cm
from server.db.models import UserNotionTask
from server.db.models.enums import SyncStatus
from server.db.repositories.caldav_events import CaldavEventsRepository
from server.services.caldav.caldav_orm import CalDavORM
from server.utils.utils import extract_uid, ensure_datetime_with_tz, is_timezone_aware
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

    async def sync_caldav_to_db(self, user_id: int, calendar_name: str, db: AsyncSession):
        await self.caldav_orm.authenticate()
        calendar = await self.caldav_orm.Calendar.get_by_name(calendar_name)
        events = await self.caldav_orm.Event.all(calendar_uid=extract_uid(calendar.id))

        deleted_events = await self.caldav_orm.Event.get_deleted_events(calendar=calendar, db=db, user_id=user_id)

        for event in events:
            event_uid = extract_uid(event.url)
            ical_url = str(event.url).strip()

            # Get RAW event datas
            event_raw = await self.repo.fetch_ical_event(
                user_id=user_id,
                calendar=calendar,
                event_url=ical_url,
                db=db
            )
            parsed_data = await self.repo.parse_ical_full(event_raw)
            title = parsed_data[0]["title"]

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

            # NOTE: If event does not exist in both CalDAV and Notion, create new records
            if not existing_caldav_event and not existing_notion_event:
                logger.info(f"Creating new event '{event.title}' (UID: {event_uid})")
                new_event = CalDavEvent(
                    user_id=user_id,
                    caldav_uid=event_uid,
                    title=event.title,
                    description=event.description,
                    start_time=ensure_datetime_with_tz(event.start),
                    end_time=ensure_datetime_with_tz(event.end),
                    caldav_url=ical_url,
                    sync_source="caldav",
                    notion_page_id=new_notion_id,
                )
                new_event_notion = UserNotionTask(
                    id=new_notion_id,
                    user_id=user_id,
                    title=event.title,
                    description=event.description,
                    start_date=ensure_datetime_with_tz(event.start),
                    end_date=ensure_datetime_with_tz(event.end),
                    notion_page_id=None,
                    notion_url=None,
                    status=None,
                    priority=None,
                    select_option=None,
                    done=False,
                    sync_source="caldav",
                    last_modified_source="caldav",
                    caldav_id=event_uid,
                    sync_status=SyncStatus.pending
                )
                db.add(new_event)
                db.add(new_event_notion)
                await db.commit()
                continue  # Move to next event

            # Determine last modified date
            raw_last_modified = parsed_data[0].get("last_modified") or parsed_data[0].get("created")
            last_modified_caldav = ensure_datetime_with_tz(raw_last_modified)

            notion_updated_at = None
            if existing_notion_event:
                notion_updated_at = ensure_datetime_with_tz(existing_notion_event.updated_at)
                if notion_updated_at is None:
                    notion_updated_at = ensure_datetime_with_tz(existing_notion_event.created_at)

            logger.debug(
                "Sync debug: existing_caldav=%s, existing_notion=%s, last_modified_caldav=%s, notion_updated_at=%s, UID=%s",
                bool(existing_caldav_event), bool(existing_notion_event),
                last_modified_caldav, notion_updated_at, event_uid
            )


            # Todo: Add functional to delete events from Notion if they are deleted in CalDAV
            if existing_caldav_event and existing_notion_event and last_modified_caldav and notion_updated_at:

                # =======================
                # Sync CalDAV → Notion
                # =======================
                if last_modified_caldav > notion_updated_at:
                    logger.info(f"[CalDAV → Notion] Updating Notion task '{event.title}' (UID: {event_uid})")
                    existing_notion_event.title = event.title
                    existing_notion_event.description = event.description
                    existing_notion_event.start_date = ensure_datetime_with_tz(event.start)
                    existing_notion_event.end_date = ensure_datetime_with_tz(event.end)
                    existing_notion_event.caldav_id = event_uid
                    existing_notion_event.sync_status = SyncStatus.pending
                    existing_notion_event.last_modified_source = "caldav"
                    existing_notion_event.updated_at = last_modified_caldav

                    existing_caldav_event.sync_source = "caldav"
                    existing_caldav_event.last_modified_source = "caldav"
                    existing_caldav_event.title = event.title
                    existing_caldav_event.description = event.description
                    existing_caldav_event.start_time = ensure_datetime_with_tz(event.start)
                    existing_caldav_event.end_time = ensure_datetime_with_tz(event.end)
                    existing_caldav_event.caldav_url = ical_url
                    await db.commit()

                # =======================
                # Sync Notion → CalDAV
                # =======================
                elif notion_updated_at > last_modified_caldav:
                    logger.info(f"[Notion → CalDAV] Updating CalDAV event '{event.title}' (UID: {event_uid})")
                    existing_caldav_event.title = existing_notion_event.title
                    existing_caldav_event.description = existing_notion_event.description
                    existing_caldav_event.start_time = ensure_datetime_with_tz(existing_notion_event.start_date)
                    existing_caldav_event.end_time = ensure_datetime_with_tz(existing_notion_event.end_date)
                    existing_caldav_event.caldav_url = ical_url
                    existing_caldav_event.sync_source = "notion"
                    existing_caldav_event.last_modified_source = "notion"
                    existing_caldav_event.updated_at = notion_updated_at

                    existing_notion_event.sync_status = SyncStatus.pending
                    existing_notion_event.last_modified_source = "notion"
                    if existing_notion_event.deleted == True:
                        existing_caldav_event.deleted = True
                        logger.debug("Marking CalDAV event as deleted")

                    await db.commit()
            else:
                logger.debug(
                    "Skipping sync for UID=%s: missing CalDAV or Notion record, or timestamps", event_uid
                )

        logger.info("CalDAV ↔ Notion sync finished successfully")

    async def sync_user_events(self):
        await self.caldav_orm.authenticate()

        calendar = await self.caldav_orm.Calendar.get_by_name("Personal")
        caldav_events = await self.caldav_orm.Event.all(calendar_uid=extract_uid(calendar.uid))

        db_events = await self.notion_orm.get_all_tasks(user_id=self.user_id)


        # 1. Sync all events from caldav to db
        await self.repo.sync_caldav_to_db(user_id=self.user_id, calendar_name="Personal")

        # 2. Sync all events from db to caldav
        await self.sync_db_to_caldav()
