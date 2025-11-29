import asyncio
import datetime
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from server.db.models import UserNotionTask
from server.db.models.enums import SyncStatus
from server.services.caldav.utils.caldav_orm import CalDavORM
from server.utils.utils import extract_uid, ensure_datetime_with_tz
from server.db.repositories.notion_tasks import NotionTaskRepository
from server.db.models.caldav_events import CalDavEvent
from server.app.core.logging_config import logger
from sqlalchemy import select


class SyncService:
    def __init__(self, user_id):
        self.user_id = user_id
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

    async def sync_user_events(self, calendar, db: AsyncSession):

        # LWW (Last-Write-Wins) стратегия:
        # Конфликт между локальным и удалённым событием решается на основе времени последнего изменения.
        # Если remote_last_modified > local.updated_at, значит удалённое событие свежее — обновляем локальное.
        # Если local.updated_at > remote_last_modified, локальное свежее — обновляем/перезаписываем удалённое.
        # При удалении: если local.deleted_at > remote_last_modified — удаляем на remote;
        # если remote_last_modified > local.deleted_at — откатываем локальное удаление.
        # Принцип: последнее изменение всегда является источником истины.

        logger.info(f"Syncing events for user ID: {self.user_id}")
        calendar_uid = extract_uid(calendar.url)
        logger.debug(f"Calendar UID: {calendar_uid}")

        caldav_events = calendar.events()

        db_events = await self.notion_orm.get_all_tasks(user_id=self.user_id)

        await self.caldav_orm.authenticate()

        for event in caldav_events:
            raw_ical_event = await self.caldav_orm.Event.fetch_ical_event(user_id=self.user_id, calendar=calendar, event_url=event.url, db=db)

            if not raw_ical_event or raw_ical_event.strip() == "":
                logger.warning("Skipping empty ICS event")
                continue

            parsed_ical_data = await self.caldav_orm.Event.parse_ical_full(raw_ical_event)

            title = parsed_ical_data[0]["title"]
            caldav_event_uid = parsed_ical_data[0]["uid"] # + ".ics"
            remote_last_modified = parsed_ical_data[0].get("last_modified") or parsed_ical_data[0].get("created")

            logger.info(f"Start syncing event: {title}")
            logger.debug(f"Last modified date: {remote_last_modified}")

            # Find if possible existing event in DB
            try:
                stmt = select(CalDavEvent).where(CalDavEvent.user_id == self.user_id, CalDavEvent.caldav_uid == caldav_event_uid)
                result = await db.execute(stmt)
                local_caldav_event = result.scalars().first()
            except Exception as e:
                logger.error(f"Error while searching for event: {e}")
                continue

            logger.debug(f"Looking for event: {caldav_event_uid}")
            if local_caldav_event:
                logger.debug(f"Found event: {caldav_event_uid}")
            else:
                logger.debug(f"Event not found in DB: {caldav_event_uid}")

            # Step 1: Creating logic
            if event and not local_caldav_event:
                # Todo: If task does not exist in DB, create it
                start_time = parsed_ical_data[0]["start"]
                end_time = parsed_ical_data[0]["end"]

                logger.debug(f"Data type: {type(start_time)}")
                try:
                    new_caldav_event = CalDavEvent(
                        user_id=self.user_id,
                        caldav_uid=caldav_event_uid,
                        caldav_url=str(event.url),
                        title=title,
                        description=parsed_ical_data[0]["description"],
                        start_time=start_time,
                        end_time=end_time,
                        sync_source="caldav",
                        last_synced_at=datetime.datetime.now(datetime.timezone.utc)
                    )
                    db.add(new_caldav_event)
                    await db.commit()
                    logger.info(f"Event created: {title}")
                except Exception as e:
                    logger.error(f"Error while creating new event: {e}")
                    continue

            # Step 2: Updating logic
            if local_caldav_event and event:
                # Step 2.1: If local event is marked deleted, un-delete only when remote last_modified is newer (LWW)
                if local_caldav_event.deleted:
                    # Todo: If last modified date is more fresh from remote, create event in DB
                    if remote_last_modified > local_caldav_event.deleted_at:
                        logger.debug(f"Unmarking event as  deleted: {title}")
                        local_caldav_event.deleted = False
                        local_caldav_event.deleted_at = None
                        db.add(local_caldav_event)
                        await db.commit()
                        logger.info(f"Event unmarked as deleted: {title}")
                    continue

                # Step 2.2: Update local event only if remote last_modified is newer (LWW)
                if remote_last_modified > local_caldav_event.updated_at:
                    logger.debug(f"Updating local event: {title}")
                    try:
                        local_caldav_event.title = title
                        local_caldav_event.description = parsed_ical_data[0]["description"]
                        local_caldav_event.start_time = parsed_ical_data[0]["start"]
                        local_caldav_event.end_time = parsed_ical_data[0]["end"]
                        local_caldav_event.last_synced_at = datetime.datetime.now(datetime.timezone.utc)
                        await db.commit()
                        await db.refresh(local_caldav_event)
                        logger.info(f"Local event updated: {title}")
                    except Exception as e:
                        logger.error(f"Error while updating local event: {e}")

                # Step 2.3: Update remote event only if local last_modified is newer (LWW)
                if local_caldav_event.updated_at > remote_last_modified:
                    # Todo: Update event in CalDav server
                    local_title = local_caldav_event.title
                    await self.caldav_orm.Event.update(event, title=local_title)
                    logger.debug(f"Updating remote event: {local_title}")

    async def get_deleted_events_from_caldav(self, calendar, db: AsyncSession) -> list[dict]:
        """
        Detect deleted events by comparing local DB records with remote CalDAV events.

        This function identifies events that exist in the local database but have been
        deleted from the iCloud CalDAV server. It uses modern CalDAV sync practices by
        comparing UIDs between local and remote sources.

        Args:
            calendar: CalDAV calendar object to check against
            db: AsyncSession for database operations

        Returns:
            list[dict]: List of deleted events with their details:
                - caldav_uid: str
                - title: str
                - deleted_at: datetime (current timestamp)
                - local_event: CalDavEvent object

        Example:
            deleted = await sync_service.get_deleted_events_from_caldav(calendar, db)
            for event in deleted:
                logger.info(f"Event '{event['title']}' was deleted remotely")
        """
        logger.info(f"Checking for deleted events for user {self.user_id}")

        try:
            # Get all local CalDAV events for this user
            stmt = select(CalDavEvent).where(
                CalDavEvent.user_id == self.user_id,
                CalDavEvent.deleted == False
            )
            result = await db.execute(stmt)
            local_events = result.scalars().all()

            # Create a mapping of local event UIDs
            local_uids = {event.caldav_uid: event for event in local_events}
            logger.debug(f"Found {len(local_uids)} local events")

            # Get all remote CalDAV events
            def _get_remote_events():
                try:
                    return calendar.events()
                except Exception as e:
                    logger.error(f"Failed to fetch remote events: {e}")
                    return []

            remote_events = await asyncio.to_thread(_get_remote_events)

            # Extract UIDs from remote events
            remote_uids = set()
            for event in remote_events:
                try:
                    event_uid = extract_uid(event.url)
                    remote_uids.add(event_uid)
                except Exception as e:
                    logger.warning(f"Failed to extract UID from remote event: {e}")
                    continue

            logger.debug(f"Found {len(remote_uids)} remote events")

            # Find events that exist locally but not remotely (deleted events)
            deleted_event_uids = set(local_uids.keys()) - remote_uids

            # Build detailed list of deleted events
            deleted_events = []
            for uid in deleted_event_uids:
                local_event = local_uids[uid]
                deleted_events.append({
                    "caldav_uid": uid,
                    "title": local_event.title,
                    "deleted_at": datetime.datetime.now(datetime.timezone.utc),
                    "local_event": local_event
                })
                logger.info(f"Detected deleted event: '{local_event.title}' (UID: {uid})")

            logger.info(f"Total deleted events detected: {len(deleted_events)}")
            return deleted_events

        except Exception as e:
            logger.error(f"Error detecting deleted events: {e}", exc_info=True)
            return []

    async def mark_events_as_deleted(self, deleted_events: list[dict], db: AsyncSession) -> int:
        """
        Mark events as deleted in the database.

        This function takes the output from get_deleted_events_from_caldav and
        updates the database to mark these events as deleted.

        Args:
            deleted_events: List of deleted event dicts from get_deleted_events_from_caldav
            db: AsyncSession for database operations

        Returns:
            int: Number of events marked as deleted

        Example:
            deleted = await sync_service.get_deleted_events_from_caldav(calendar, db)
            count = await sync_service.mark_events_as_deleted(deleted, db)
            logger.info(f"Marked {count} events as deleted")
        """
        marked_count = 0

        for deleted_event in deleted_events:
            try:
                local_event = deleted_event["local_event"]
                deleted_at = deleted_event["deleted_at"]

                # Update the event in DB
                local_event.deleted = True
                local_event.deleted_at = deleted_at

                db.add(local_event)
                marked_count += 1

                logger.info(f"Marked event '{local_event.title}' as deleted")

            except Exception as e:
                logger.error(f"Failed to mark event as deleted: {e}")
                continue

        try:
            await db.commit()
            logger.info(f"Successfully marked {marked_count} events as deleted")
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to commit deleted events: {e}")
            raise

        return marked_count
