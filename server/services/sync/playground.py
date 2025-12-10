import datetime
import os
import sys
import asyncio
from datetime import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from server.db.deps import async_get_db_cm
from server.utils.utils import ensure_datetime_with_tz

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from server.services.sync.utils.caldav_orm import CalDavORM
from server.services.sync.sync_manager import SyncService
from server.app.core.logging_config import logger

# import pretty_errors
from rich.traceback import install
install(show_locals=True)  # Add at startup

async def test_deleted_events_detection():
    """
    Comprehensive test for deleted events detection.
    Tests both detection and marking functionality.
    """
    logger.info("=" * 60)
    logger.info("TESTING DELETED EVENTS DETECTION")
    logger.info("=" * 60)

    sync_service = SyncService(user_id=3)
    orm = CalDavORM(user_id=3)

    await orm.authenticate()
    calendar_name = "Work"
    calendar = await orm.Calendar.get_by_name(calendar_name)

    if not calendar:
        logger.error(f"Calendar '{calendar_name}' not found!")
        return

    async with async_get_db_cm() as db:
        # Get local events to show comparison
        from sqlalchemy import select
        from server.db.models.caldav_events import CalDavEvent

        stmt = select(CalDavEvent).where(
            CalDavEvent.user_id == 3,
            CalDavEvent.deleted == False
        )
        result = await db.execute(stmt)
        local_events = result.scalars().all()

        logger.info(f"\n📊 LOCAL DATABASE EVENTS: {len(local_events)}")
        for i, event in enumerate(local_events[:5], 1):  # Show first 5
            logger.info(f"  {i}. '{event.title}' - UID: {event.caldav_uid[:20]}...")
        if len(local_events) > 5:
            logger.info(f"  ... and {len(local_events) - 5} more")

        # Get remote events
        logger.info(f"\n🔄 Fetching remote CalDAV events...")
        remote_events = await orm.Event.all(calendar_uid=calendar.id)
        logger.info(f"📡 REMOTE CALDAV EVENTS: {len(remote_events)}")
        for i, event in enumerate(remote_events[:5], 1):  # Show first 5
            logger.info(f"  {i}. '{event.title}' - UID: {event.uid[:20]}...")
        if len(remote_events) > 5:
            logger.info(f"  ... and {len(remote_events) - 5} more")

        # Step 1: Detect deleted events
        logger.info(f"\n🔍 DETECTING DELETED EVENTS...")
        deleted_events = await sync_service.get_deleted_events_from_caldav(
            calendar=calendar,
            db=db
        )

        logger.info(f"\n" + "=" * 60)
        if len(deleted_events) == 0:
            logger.info("✅ No deleted events found - all local events exist remotely")
            logger.info("=" * 60)

            # Show which events are in DB but check their remote status
            logger.info("\n💡 TIP: To test deletion detection:")
            logger.info("   1. Delete an event from iCloud Calendar")
            logger.info("   2. Keep the event in your local database")
            logger.info("   3. Run this script again")
            logger.info("   The deleted event will be detected!")
        else:
            logger.info(f"🗑️  FOUND {len(deleted_events)} DELETED EVENTS:")
            logger.info("=" * 60)
            for i, event in enumerate(deleted_events, 1):
                logger.info(f"\n  Event #{i}:")
                logger.info(f"    Title: {event['title']}")
                logger.info(f"    UID: {event['caldav_uid']}")
                logger.info(f"    Detected at: {event['deleted_at']}")

            # Step 2: Test marking events as deleted
            logger.info(f"\n🏷️  TESTING MARK AS DELETED...")
            confirm = input(f"\nDo you want to mark these {len(deleted_events)} events as deleted in DB? (yes/no): ")

            if confirm.lower() in ['yes', 'y']:
                marked_count = await sync_service.mark_events_as_deleted(
                    deleted_events=deleted_events,
                    db=db
                )
                logger.info(f"\n✅ Successfully marked {marked_count} events as deleted!")
            else:
                logger.info("❌ Skipped marking events as deleted")

async def simulate_deleted_event_test():
    """
    Create a test event in DB only (not in CalDAV) to simulate a deleted event.
    This helps test the detection functionality without actually deleting from iCloud.
    """
    logger.info("=" * 60)
    logger.info("SIMULATING DELETED EVENT TEST")
    logger.info("=" * 60)

    from server.db.models.caldav_events import CalDavEvent
    import uuid
    from datetime import datetime, timezone

    sync_service = SyncService(user_id=3)
    orm = CalDavORM(user_id=3)

    await orm.authenticate()
    calendar = await orm.Calendar.get_by_name("Work")

    if not calendar:
        logger.error("Calendar 'Work' not found!")
        return

    async with async_get_db_cm() as db:
        # Create a fake event in DB only
        fake_event = CalDavEvent(
            user_id=3,
            caldav_uid=f"SIMULATED-TEST-EVENT-{uuid.uuid4()}.ics",
            caldav_url=f"https://caldav.icloud.com/test-{uuid.uuid4()}.ics",
            title="🧪 SIMULATED DELETED EVENT (for testing)",
            description="This event exists only in DB, not in CalDAV",
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            sync_source="caldav",
            deleted=False
        )

        db.add(fake_event)
        await db.commit()
        await db.refresh(fake_event)

        logger.info(f"\n✅ Created simulated event in DB:")
        logger.info(f"   Title: {fake_event.title}")
        logger.info(f"   UID: {fake_event.caldav_uid}")
        logger.info(f"   ID: {fake_event.id}")

        # Now test detection
        logger.info(f"\n🔍 Testing detection...")
        deleted_events = await sync_service.get_deleted_events_from_caldav(
            calendar=calendar,
            db=db
        )

        # Check if our simulated event was detected
        simulated_found = any(e['caldav_uid'] == fake_event.caldav_uid for e in deleted_events)

        if simulated_found:
            logger.info(f"\n✅ SUCCESS! The simulated event was detected as deleted!")
            logger.info(f"   This proves the detection function works correctly.")

            # Test marking it as deleted
            logger.info(f"\n🏷️  Testing mark_events_as_deleted...")
            marked = await sync_service.mark_events_as_deleted(deleted_events, db)
            logger.info(f"✅ Marked {marked} events as deleted")

            # Verify it's marked
            await db.refresh(fake_event)
            logger.info(f"\n✅ Verification:")
            logger.info(f"   Event.deleted = {fake_event.deleted}")
            logger.info(f"   Event.deleted_at = {fake_event.deleted_at}")
        else:
            logger.error(f"\n❌ FAILED! Simulated event was NOT detected.")
            logger.error(f"   Expected to find UID: {fake_event.caldav_uid}")

        # Cleanup
        logger.info(f"\n🧹 Cleaning up test event...")
        await db.delete(fake_event)
        await db.commit()
        logger.info(f"✅ Test event removed from database")

async def show_all_events_comparison():
    """
    Show detailed comparison of local vs remote events.
    Helps identify which events might be deleted.
    """
    logger.info("=" * 60)
    logger.info("DETAILED EVENT COMPARISON")
    logger.info("=" * 60)

    orm = CalDavORM(user_id=3)
    await orm.authenticate()
    calendar = await orm.Calendar.get_by_name("Work")

    if not calendar:
        logger.error("Calendar 'Work' not found!")
        return

    async with async_get_db_cm() as db:
        from sqlalchemy import select
        from server.db.models.caldav_events import CalDavEvent
        from server.utils.utils import extract_uid

        # Get local events
        stmt = select(CalDavEvent).where(
            CalDavEvent.user_id == 3,
            CalDavEvent.deleted == False
        )
        result = await db.execute(stmt)
        local_events = result.scalars().all()

        # Get remote events
        remote_events = await orm.Event.all(calendar_uid=calendar.id)

        # Create mappings
        local_map = {e.caldav_uid: e for e in local_events}
        remote_map = {extract_uid(e.url): e for e in remote_events}

        logger.info(f"\n📊 STATISTICS:")
        logger.info(f"   Local events: {len(local_map)}")
        logger.info(f"   Remote events: {len(remote_map)}")
        logger.info(f"   New remote events: {len(set(remote_map.keys()) - set(local_map.keys()))}")
        logger.info(f"   Deleted events: {len(set(local_map.keys()) - set(remote_map.keys()))}")

        # Show deleted events
        deleted_uids = set(local_map.keys()) - set(remote_map.keys())
        if deleted_uids:
            logger.info(f"\n🗑️  DELETED EVENTS (in DB but not in CalDAV):")
            for uid in deleted_uids:
                event = local_map[uid]
                logger.info(f"   - '{event.title}' (UID: {uid[:30]}...)")

        # Show new events
        new_uids = set(remote_map.keys()) - set(local_map.keys())
        if new_uids:
            logger.info(f"\n✨ NEW EVENTS (in CalDAV but not in DB):")
            for uid in new_uids:
                event = remote_map[uid]
                logger.info(f"   - '{event.title}' (UID: {uid[:30]}...)")

async def run_test():
    """Main entry point for testing."""
    print("\nChoose a test to run:")
    print("1. Test deleted events detection (real check)")
    print("2. Simulate a deleted event (creates fake event in DB)")
    print("3. Show detailed event comparison")
    print("4. Run all tests")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice == "1":
        await test_deleted_events_detection()
    elif choice == "2":
        await simulate_deleted_event_test()
    elif choice == "3":
        await show_all_events_comparison()
    elif choice == "4":
        await show_all_events_comparison()
        print("\n" + "=" * 60 + "\n")
        await test_deleted_events_detection()
        print("\n" + "=" * 60 + "\n")
        await simulate_deleted_event_test()
    else:
        logger.error("Invalid choice!")


async def manual_sync():
    """Main entry point for manual testing."""
    orm = CalDavORM(user_id=3)
    sync_service = SyncService(user_id=3)
    await orm.authenticate()
    calendar_name = "Calnio"
    calendar = await orm.Calendar.get_by_name(calendar_name)
    if not calendar:
        logger.error(f"Calendar '{calendar_name}' not found!")
        return
    async with async_get_db_cm() as db:
        await sync_service.sync_user_events(db=db, calendar=calendar)

async def sync():
    orm = CalDavORM(user_id=3)
    sync_service = SyncService(user_id=3)
    await orm.authenticate()
    calendar_name = "Calnio"
    calendar = await orm.Calendar.get_by_name(calendar_name)
    if not calendar:
        logger.error(f"Calendar '{calendar_name}' not found!")
        return
    async with async_get_db_cm() as db:
        await sync_service.sync_user_events(calendar=calendar, db=db)


scheduler = AsyncIOScheduler()

async def scheduler_sync():
    logger.info("Starting Calnio sync scheduler")
    sync_interval = 30
    scheduler.add_job(
        sync,
        "interval",
        seconds=sync_interval,
        replace_existing=False,
        name="sync_user_events"
    )

    try:
        await sync()
        scheduler.start()
        logger.info(f"Scheduler started | interval={sync_interval}s")
        # This prevent from quitting the script
        try:
            while True:
                await asyncio.sleep(5)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Shutting down scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler stopped successfully")

    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()

async def main():
    remote_lst_mdf = ensure_datetime_with_tz(datetime.datetime.fromisoformat("2025-12-09 02:01:59+00:00"))
    local_dlt = ensure_datetime_with_tz(datetime.datetime.fromisoformat("2025-12-08 19:14:08.543000+00:00"))
    logger.info(f"Remote last modified: {remote_lst_mdf} | Local last deleted: {local_dlt}")
    if remote_lst_mdf < local_dlt:
        logger.info("Remote is older")
    else:
        logger.info("Local is older")

    await sync()

if __name__ == "__main__":
    asyncio.run(scheduler_sync())