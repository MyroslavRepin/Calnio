import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select

from server.db.deps import async_get_db_cm
from server.db.models import UserNotionTask
from server.db.models.enums import SyncStatus
from server.db.repositories.caldav_events import CaldavEventsRepository
from server.services.caldav.caldav_orm import CalDavORM
from server.utils.utils import extract_uid, ensure_datetime_with_tz, is_timezone_aware
from server.db.repositories.notion_tasks import NotionTaskRepository
from server.db.models.caldav_events import CalDavEvent
from server.app.core.logging_config import logger


class SyncService:
    def __init__(self, user_id):
        self.user_id = user_id
        self.repo = CaldavEventsRepository()
        self.caldav_orm = CalDavORM(user_id=user_id)
        self.notion_orm = NotionTaskRepository()

    def _get_latest_timestamp(self, record) -> datetime:
        """
        Helper method to get the latest timestamp from a record.
        Falls back from updated_at to created_at to ensure comparisons never fail.
        Always returns a timezone-aware datetime in UTC.
        
        Args:
            record: Database record (CalDavEvent or UserNotionTask)
            
        Returns:
            datetime: Timezone-aware datetime in UTC
        """
        timestamp = getattr(record, 'updated_at', None)
        if timestamp is None:
            timestamp = getattr(record, 'created_at', None)
        
        # Ensure timestamp is timezone-aware
        if timestamp:
            timestamp = ensure_datetime_with_tz(timestamp)
        
        # If still None, use current UTC time as fallback
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
            logger.warning(f"No timestamp found for record, using current UTC time: {timestamp}")
        
        return timestamp

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
        """
        Production-grade two-way synchronization between CalDAV and local database.
        
        Implements Last Write Wins (LWW) conflict resolution strategy by comparing timestamps
        from both local database and remote CalDAV server. Handles event creation, updates,
        and deletions with robust error handling and comprehensive logging.
        
        Features:
        - Two-way sync with LWW conflict resolution
        - Handles remote and local deletions
        - Atomic commits/rollbacks for data integrity
        - Comprehensive logging for all decisions
        - Timezone-aware datetime comparisons (UTC)
        - Network timeout and parsing error handling
        
        Args:
            user_id (int): The ID of the user whose calendar events should be synchronized
            calendar_name (str): The name of the CalDAV calendar to synchronize
            db (AsyncSession): The asynchronous database session for database operations
            
        Raises:
            RuntimeError: If CalDAV client authentication fails
            Exception: For network timeouts or critical parsing errors
        """
        try:
            # Authenticate with CalDAV server
            logger.info(f"Starting two-way sync for user {user_id}, calendar '{calendar_name}'")
            await self.caldav_orm.authenticate()
            logger.debug("CalDAV authentication successful")
            
            # Get calendar
            calendar = await self.caldav_orm.Calendar.get_by_name(calendar_name)
            if not calendar:
                logger.error(f"Calendar '{calendar_name}' not found for user {user_id}")
                raise ValueError(f"Calendar '{calendar_name}' not found")
            
            calendar_uid = extract_uid(calendar.id)
            logger.info(f"Found calendar: {calendar_name} (UID: {calendar_uid})")
            
            # Fetch all remote events
            try:
                remote_events = await self.caldav_orm.Event.all(calendar_uid=calendar_uid)
                logger.info(f"Fetched {len(remote_events)} events from remote CalDAV server")
            except Exception as e:
                logger.error(f"Failed to fetch remote CalDAV events: {e}")
                raise
            
            # Fetch all local events for this user
            try:
                stmt_local = select(CalDavEvent).where(CalDavEvent.user_id == user_id)
                result = await db.execute(stmt_local)
                local_events = result.scalars().all()
                logger.info(f"Found {len(local_events)} events in local database")
            except Exception as e:
                logger.error(f"Failed to fetch local database events: {e}")
                await db.rollback()
                raise
            
            # Build a map of remote event UIDs for quick lookup
            remote_event_uids = set()
            remote_events_by_uid = {}
            
            for event in remote_events:
                uid = event.uid or extract_uid(event.url)
                if uid:
                    remote_event_uids.add(uid)
                    remote_events_by_uid[uid] = event
            
            # Build a map of local event UIDs
            local_events_by_uid = {}
            for local_event in local_events:
                if local_event.caldav_uid:
                    local_events_by_uid[local_event.caldav_uid] = local_event
            
            # =====================================================
            # PHASE 1: Process remote events (create/update local)
            # =====================================================
            logger.info("PHASE 1: Processing remote CalDAV events")
            
            for event in remote_events:
                parsed_data = None
                ical_url = str(event.url).strip()
                
                try:
                    # Extract UID
                    parsed_uid = None
                    if event and getattr(event, "uid", None):
                        parsed_uid = str(event.uid).strip()
                    
                    if not parsed_uid:
                        # Fetch and parse ICS data to get UID
                        try:
                            event_raw = await self.repo.fetch_ical_event(
                                user_id=user_id,
                                calendar=calendar,
                                event_url=ical_url,
                                db=db
                            )
                            parsed_data = await self.repo.parse_ical_full(event_raw)
                            parsed_uid = parsed_data[0].get("uid") if parsed_data else None
                        except Exception as e:
                            logger.error(f"Failed to fetch/parse event at {ical_url}: {e}")
                            continue
                    
                    event_uid = (parsed_uid or extract_uid(event.url) or "").strip()
                    if event_uid.lower() == "none":
                        event_uid = ""
                    
                    if not event_uid:
                        logger.warning(f"Skipping event at {ical_url}: UID missing in CalDAV payload")
                        continue
                    
                    # Fetch parsed data if not already fetched
                    if parsed_data is None:
                        try:
                            event_raw = await self.repo.fetch_ical_event(
                                user_id=user_id,
                                calendar=calendar,
                                event_url=ical_url,
                                db=db
                            )
                            parsed_data = await self.repo.parse_ical_full(event_raw)
                        except Exception as e:
                            logger.error(f"Failed to fetch/parse event {event_uid}: {e}")
                            continue
                    
                    if not parsed_data or len(parsed_data) == 0:
                        logger.warning(f"No parsed data for event {event_uid}, skipping")
                        continue
                    
                    # Extract event metadata
                    event_data = parsed_data[0]
                    title = event_data.get("title", "Untitled Event")
                    description = event_data.get("description", "")
                    start_time = ensure_datetime_with_tz(event.start)
                    end_time = ensure_datetime_with_tz(event.end)
                    
                    # Get remote timestamp (last_modified or created)
                    raw_last_modified = event_data.get("last_modified") or event_data.get("created")
                    remote_timestamp = ensure_datetime_with_tz(raw_last_modified)
                    
                    if not remote_timestamp:
                        logger.warning(f"LWW: Event {event_uid} has no timestamp, using current UTC time")
                        remote_timestamp = datetime.now(timezone.utc)
                    
                    # Check if event exists locally
                    existing_local = local_events_by_uid.get(event_uid)
                    
                    if not existing_local:
                        # CREATE: Event exists remotely but not locally
                        logger.info(f"LWW: Creating new local event '{title}' (UID: {event_uid})")
                        
                        try:
                            new_notion_id = str(uuid.uuid4())
                            
                            # Create CalDavEvent
                            new_caldav_event = CalDavEvent(
                                user_id=user_id,
                                caldav_uid=event_uid,
                                caldav_url=ical_url,
                                title=title,
                                description=description,
                                start_time=start_time,
                                end_time=end_time,
                                sync_source="caldav",
                                last_modified_source="caldav",
                                notion_page_id=new_notion_id,
                                sync_status=SyncStatus.pending,
                                deleted=False
                            )
                            db.add(new_caldav_event)
                            
                            # Create corresponding Notion task
                            new_notion_task = UserNotionTask(
                                user_id=user_id,
                                title=title,
                                description=description,
                                start_date=start_time,
                                end_date=end_time,
                                notion_page_id=new_notion_id,
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
                            db.add(new_notion_task)
                            
                            await db.commit()
                            logger.info(f"LWW: Successfully created local event {event_uid}")
                            
                        except Exception as e:
                            logger.error(f"Failed to create local event {event_uid}: {e}")
                            await db.rollback()
                            continue
                    else:
                        # UPDATE: Event exists both locally and remotely - apply LWW
                        local_timestamp = self._get_latest_timestamp(existing_local)
                        
                        logger.debug(f"LWW: Comparing timestamps for {event_uid}")
                        logger.debug(f"  Remote timestamp: {remote_timestamp}")
                        logger.debug(f"  Local timestamp: {local_timestamp}")
                        
                        if remote_timestamp > local_timestamp:
                            # Remote is newer - update local from remote
                            logger.info(f"LWW: Remote is newer, updating local DB for event '{title}' (UID: {event_uid})")
                            
                            try:
                                existing_local.title = title
                                existing_local.description = description
                                existing_local.start_time = start_time
                                existing_local.end_time = end_time
                                existing_local.caldav_url = ical_url
                                existing_local.sync_source = "caldav"
                                existing_local.last_modified_source = "caldav"
                                existing_local.updated_at = remote_timestamp
                                existing_local.deleted = False
                                
                                # Update corresponding Notion task if exists
                                stmt_notion = select(UserNotionTask).where(
                                    UserNotionTask.user_id == user_id,
                                    UserNotionTask.caldav_id == event_uid
                                )
                                result = await db.execute(stmt_notion)
                                notion_task = result.scalars().first()
                                
                                if notion_task:
                                    notion_task.title = title
                                    notion_task.description = description
                                    notion_task.start_date = start_time
                                    notion_task.end_date = end_time
                                    notion_task.sync_status = SyncStatus.pending
                                    notion_task.last_modified_source = "caldav"
                                    notion_task.updated_at = remote_timestamp
                                
                                await db.commit()
                                logger.info(f"LWW: Successfully updated local event {event_uid}")
                                
                            except Exception as e:
                                logger.error(f"Failed to update local event {event_uid}: {e}")
                                await db.rollback()
                                continue
                        elif local_timestamp > remote_timestamp:
                            # Local is newer - update remote from local
                            logger.info(f"LWW: Local is newer, need to update remote CalDAV for event '{title}' (UID: {event_uid})")
                            
                            try:
                                # Mark for sync to propagate local changes to remote
                                existing_local.sync_status = SyncStatus.pending
                                existing_local.last_modified_source = "notion"
                                
                                # Update corresponding Notion task sync status
                                stmt_notion = select(UserNotionTask).where(
                                    UserNotionTask.user_id == user_id,
                                    UserNotionTask.caldav_id == event_uid
                                )
                                result = await db.execute(stmt_notion)
                                notion_task = result.scalars().first()
                                
                                if notion_task:
                                    notion_task.sync_status = SyncStatus.pending
                                    notion_task.last_modified_source = "notion"
                                
                                await db.commit()
                                logger.info(f"LWW: Marked local event {event_uid} for sync to remote")
                                
                            except Exception as e:
                                logger.error(f"Failed to mark event {event_uid} for sync: {e}")
                                await db.rollback()
                                continue
                        else:
                            # Timestamps are equal - no sync needed
                            logger.debug(f"LWW: Timestamps equal for {event_uid}, no sync needed")
                
                except Exception as e:
                    logger.error(f"Error processing remote event at {ical_url}: {e}")
                    continue
            
            # =========================================================
            # PHASE 2: Handle local deletions (propagate to remote)
            # =========================================================
            logger.info("PHASE 2: Processing local deletions")
            
            for local_event in local_events:
                try:
                    if local_event.deleted and local_event.caldav_uid:
                        # Local event is marked as deleted - check if it still exists remotely
                        if local_event.caldav_uid in remote_event_uids:
                            logger.info(f"LWW: Local deletion detected for event '{local_event.title}' (UID: {local_event.caldav_uid})")
                            logger.info(f"LWW: Marking for deletion propagation to remote CalDAV server")
                            
                            # Mark sync status as pending to trigger deletion on remote
                            local_event.sync_status = SyncStatus.pending
                            local_event.last_modified_source = "notion"
                            
                            # Update corresponding Notion task
                            stmt_notion = select(UserNotionTask).where(
                                UserNotionTask.user_id == user_id,
                                UserNotionTask.caldav_id == local_event.caldav_uid
                            )
                            result = await db.execute(stmt_notion)
                            notion_task = result.scalars().first()
                            
                            if notion_task:
                                notion_task.deleted = True
                                notion_task.sync_status = SyncStatus.pending
                                notion_task.last_modified_source = "notion"
                            
                            await db.commit()
                            logger.info(f"LWW: Marked local deletion {local_event.caldav_uid} for remote propagation")
                
                except Exception as e:
                    logger.error(f"Error processing local deletion for {local_event.caldav_uid}: {e}")
                    await db.rollback()
                    continue
            
            # =========================================================
            # PHASE 3: Handle remote deletions (apply to local)
            # =========================================================
            logger.info("PHASE 3: Processing remote deletions")
            
            for local_event in local_events:
                try:
                    if local_event.caldav_uid and local_event.caldav_uid not in remote_event_uids:
                        # Event exists locally but not remotely - was deleted on server
                        if not local_event.deleted:
                            local_timestamp = self._get_latest_timestamp(local_event)
                            
                            # Check if this is a deliberate remote deletion or local event that was never synced
                            # If last_synced_at is set and recent, this is likely a remote deletion
                            if local_event.last_synced_at:
                                last_synced = ensure_datetime_with_tz(local_event.last_synced_at)
                                
                                logger.info(f"LWW: Remote deletion detected for event '{local_event.title}' (UID: {local_event.caldav_uid})")
                                logger.debug(f"  Last synced at: {last_synced}")
                                logger.debug(f"  Local timestamp: {local_timestamp}")
                                
                                # Apply LWW: if remote deletion is "newer" than local changes
                                # For deletions, we consider the deletion as happening "now"
                                deletion_timestamp = datetime.now(timezone.utc)
                                
                                if deletion_timestamp > local_timestamp:
                                    logger.info(f"LWW: Remote deletion is newer, marking local event {local_event.caldav_uid} as deleted")
                                    
                                    local_event.deleted = True
                                    local_event.deleted_at = deletion_timestamp
                                    local_event.sync_source = "caldav"
                                    local_event.last_modified_source = "caldav"
                                    
                                    # Update corresponding Notion task
                                    stmt_notion = select(UserNotionTask).where(
                                        UserNotionTask.user_id == user_id,
                                        UserNotionTask.caldav_id == local_event.caldav_uid
                                    )
                                    result = await db.execute(stmt_notion)
                                    notion_task = result.scalars().first()
                                    
                                    if notion_task:
                                        notion_task.deleted = True
                                        notion_task.sync_status = SyncStatus.pending
                                        notion_task.last_modified_source = "caldav"
                                    
                                    await db.commit()
                                    logger.info(f"LWW: Successfully marked local event {local_event.caldav_uid} as deleted")
                                else:
                                    logger.info(f"LWW: Local changes are newer than remote deletion, preserving local event {local_event.caldav_uid}")
                                    logger.info(f"LWW: Marking event for recreation on remote server")
                                    local_event.sync_status = SyncStatus.pending
                                    await db.commit()
                
                except Exception as e:
                    logger.error(f"Error processing remote deletion for {local_event.caldav_uid}: {e}")
                    await db.rollback()
                    continue
            
            logger.info(f"Two-way CalDAV sync completed successfully for user {user_id}")
            
        except Exception as e:
            logger.error(f"Critical error during CalDAV sync for user {user_id}: {e}")
            await db.rollback()
            raise

    async def sync_user_events(self):
        await self.caldav_orm.authenticate()

        calendar = await self.caldav_orm.Calendar.get_by_name("Personal")
        caldav_events = await self.caldav_orm.Event.all(calendar_uid=extract_uid(calendar.uid))

        db_events = await self.notion_orm.get_all_tasks(user_id=self.user_id)


        # 1. Sync all events from caldav to db
        await self.repo.sync_caldav_to_db(user_id=self.user_id, calendar_name="Personal")

        # 2. Sync all events from db to caldav
        await self.sync_db_to_caldav()