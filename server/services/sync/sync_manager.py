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

        async with async_get_db_cm() as db:
            for event in events:
                ical_url = str(event.url).strip()

                event_raw = await self.repo.fetch_ical_event(
                    user_id=user_id,
                    calendar=calendar,
                    event_url=ical_url,
                    db=db
                )

                # logger.debug(f"Event RAW: {event_raw}")

                parsed_data = await self.repo.parse_ical_full(event_raw)
                title = parsed_data[0]["title"]

                # ==================================================
                # === last_modified_caldav is now either None or an ===
                # === aware datetime in UTC                        ===
                # ==================================================
                event_uid = extract_uid(event.url)
                logger.info(f"Syncing event '{event.title}' (UID: {event_uid}) for user ID: {user_id}")

                # Here I have to add a record to notion_tasks db with sync_status=pending
                stmt = select(CalDavEvent).where(
                    CalDavEvent.user_id == user_id,
                    CalDavEvent.caldav_uid == event_uid
                )
                result = await db.execute(stmt)
                existing_caldav_event = result.scalars().first()
                stmt = select(UserNotionTask).where(
                    UserNotionTask.user_id == user_id,
                    UserNotionTask.caldav_id == event_uid
                )
                result = await db.execute(stmt)
                existing_notion_event = result.scalars().first()
                new_notion_id = str(uuid.uuid4())

                # TODO: Put this code into function
                logger.debug(f"Is datetime aware: {is_timezone_aware(last_modified_caldav)}")
                logger.debug(f"Is datetime aware: {is_timezone_aware(existing_caldav_event.updated_at)}")

                # At this point we have last_modified_caldav as either
                # None or an aware datetime in UTC. Continue processing.


                # Saving new data to notion_tasks and caldav_events
                if not existing_caldav_event and not existing_notion_event:
                    logger.info(f"Creating new event '{event.title}' (UID: {event_uid})"),
                    new_event = CalDavEvent(
                        user_id=user_id,
                        caldav_uid=event_uid,
                        title=event.title,
                        description=event.description,
                        start_time=ensure_datetime_with_tz(event.start),
                        end_time=ensure_datetime_with_tz(event.end),
                        caldav_url=str(event.url),
                        sync_source="caldav",
                        notion_page_id=new_notion_id, # Making connect to the same record in UserNotionTask
                    )
                    new_event_notion = UserNotionTask(
                        id=new_notion_id,
                        user_id=user_id,
                        title=event.title,
                        description=event.description,
                        start_date=ensure_datetime_with_tz(event.start),
                        end_date=ensure_datetime_with_tz(event.end),
                        notion_page_id="", # I can't provide notion id because this record not in Notion yet
                        notion_url="", # Same for url
                        status=None,
                        priority=None,
                        select_option=None,
                        done=False,
                        sync_source="caldav",
                        last_modified_source="caldav",
                        caldav_id=event_uid,
                        sync_status=SyncStatus.pending
                     )
                    # Insert in caldav_events record notion_page_id
                    db.add(new_event)
                    db.add(new_event_notion)
                    await db.commit()

                # Getting last modified time from notion_tasks and CalDav
                notion_updated_at = None
                raw_last_modified = parsed_data[0].get("last_modified") or parsed_data[0].get("created")
                last_modified_caldav = ensure_datetime_with_tz(raw_last_modified)

                if existing_notion_event:
                    notion_updated_at = ensure_datetime_with_tz(existing_notion_event.updated_at)
                    if notion_updated_at is None:
                        notion_updated_at = ensure_datetime_with_tz(existing_notion_event.created_at)

                logger.debug(
                    f"Last modified - CalDav: {last_modified_caldav} - Notion: {notion_updated_at}")
                logger.debug(
                    f"Date Type - CalDav: {type(last_modified_caldav)} - Notion: {type(notion_updated_at)}")

                # Updating existing data in notion_tasks and caldav_events
                # Fixme: Some of datetime fields are with timezone, some without
                if existing_caldav_event and existing_notion_event and last_modified_caldav and notion_updated_at:
                    if last_modified_caldav > notion_updated_at:
                        # =====================
                        # CalDAV свежее — обновляем Notion
                        # =====================
                        logger.info(
                            f"[CalDAV→Notion] '{event.title}' (UID: {event_uid})")

                        # Notion обновление
                        existing_notion_event.title = event.title
                        existing_notion_event.description = event.description
                        existing_notion_event.start_date = ensure_datetime_with_tz(event.start)
                        existing_notion_event.end_date = ensure_datetime_with_tz(event.end)
                        existing_notion_event.caldav_id = event_uid
                        existing_notion_event.sync_status = SyncStatus.pending
                        existing_notion_event.last_modified_source = "caldav"
                        existing_notion_event.updated_at = ensure_datetime_with_tz(last_modified_caldav)

                        # CalDAV небольшое обновление — пометки о синхронизации
                        existing_caldav_event.sync_source = "caldav"
                        existing_caldav_event.last_modified_source = "caldav"
                        # обновляем только поля, которые реально поменялись, если нужно:
                        existing_caldav_event.title = event.title
                        existing_caldav_event.description = event.description
                        existing_caldav_event.start_time = ensure_datetime_with_tz(event.start)
                        existing_caldav_event.end_time = ensure_datetime_with_tz(event.end)
                        existing_caldav_event.caldav_url = str(event.url)
                        # Не трогаем updated_at, чтобы оно оставалось последним временем изменения
                        await db.commit()
                    elif notion_updated_at > last_modified_caldav:
                        # =====================
                        # Notion свежее — обновляем CalDAV
                        # =====================
                        logger.info(
                            f"[CalDAV→Notion] '{event.title}' (UID: {event_uid})")
                        # CalDAV обновление
                        existing_caldav_event.title = event.title
                        existing_caldav_event.description = event.description
                        existing_caldav_event.start_time = ensure_datetime_with_tz(event.start)
                        existing_caldav_event.end_time = ensure_datetime_with_tz(event.end)
                        existing_caldav_event.caldav_url = str(event.url)
                        existing_caldav_event.sync_source = "notion"
                        existing_caldav_event.last_modified_source = "notion"
                        existing_caldav_event.updated_at = ensure_datetime_with_tz(notion_updated_at)

                        # Notion небольшое обновление — пометки о синхронизации
                        existing_notion_event.sync_status = SyncStatus.pending
                        existing_notion_event.last_modified_source = "notion"
                        await db.commit()
                else:
                    # If we don't have both timestamps or both records, log and skip
                    logger.debug(
                        "Skipping comparison/update because one of: existing_caldav_event, existing_notion_event, last_modified_caldav or notion_updated_at is missing")

        try:
            await db.commit()
            logger.info("CalDAV events synced successfully")
        except Exception as e:
            logger.error(f"Failed to commit CalDAV sync: {e}")
            await db.rollback()

    async def sync_user_events(self):
        await self.caldav_orm.authenticate()

        calendar = await self.caldav_orm.Calendar.get_by_name("Personal")
        caldav_events = await self.caldav_orm.Event.all(calendar_uid=extract_uid(calendar.uid))

        db_events = await self.notion_orm.get_all_tasks(user_id=self.user_id)

        # Todo: Roadmap for future implementation:
        # 1. Sync all events from caldav to db - DONE
        # 2. Sync all events from db to caldav
        # 3. Sync all events from caldav to notion
        # 4. Sync all events from notion to db



        # 1. Sync all events from caldav to db
        await self.repo.sync_caldav_to_db(user_id=self.user_id, calendar_name="Personal")

        # 2. Sync all events from db to caldav
        await self.sync_db_to_caldav()

    async def sync_caldav_db_to_notion(self, user_id, db: AsyncSession, calendar_name: str = "Personal"):
        # Step 1: Get all events from CalDav
        await self.caldav_orm.authenticate()
        calendar = await self.caldav_orm.Calendar.get_by_name("Personal")
