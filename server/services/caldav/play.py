# --- Константы / настройки ---
USERNAME = "myroslavrepin@icloud.com"
APP_PASSWORD = "enbk-ajie-xawk-gvbg"

import caldav
from caldav.elements import dav, cdav
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum
import time
import json
import hashlib


class ChangeType(Enum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclass
class EventSnapshot:
    """Snapshot of an event for change detection"""
    uid: str
    href: str
    etag: str
    summary: str
    start: Optional[datetime]
    end: Optional[datetime]
    last_modified: Optional[datetime]
    raw_data: str
    captured_at: datetime = field(default_factory=datetime.now)

    def to_dict(self):
        return {
            "uid": self.uid,
            "href": self.href,
            "etag": self.etag,
            "summary": self.summary,
            "start": self.start.isoformat() if self.start else None,
            "end": self.end.isoformat() if self.end else None,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "captured_at": self.captured_at.isoformat()
        }


@dataclass
class EventChange:
    """Represents a detected change"""
    change_type: ChangeType
    detected_at: datetime
    current: Optional[EventSnapshot]
    previous: Optional[EventSnapshot]

    def to_dict(self):
        return {
            "change_type": self.change_type.value,
            "detected_at": self.detected_at.isoformat(),
            "current": self.current.to_dict() if self.current else None,
            "previous": self.previous.to_dict() if self.previous else None
        }

    def __str__(self):
        if self.change_type == ChangeType.ADDED:
            return f"[ADDED] {self.current.summary} at {self.detected_at}"
        elif self.change_type == ChangeType.DELETED:
            return f"[DELETED] {self.previous.summary} at {self.detected_at}"
        else:
            return f"[MODIFIED] {self.current.summary} at {self.detected_at}"


class AppleCalendarWatcher:
    """
    Watches Apple Calendar for changes via CalDAV polling.

    Usage:
        watcher = AppleCalendarWatcher(
            username="your@icloud.com",
            app_password="xxxx-xxxx-xxxx-xxxx"
        )
        watcher.watch(interval=10, on_change=my_callback)
    """

    CALDAV_URL = "https://caldav.icloud.com"

    def __init__(self, username: str, app_password: str, calendar_name: str = None):
        self.username = username
        self.app_password = app_password
        self.calendar_name = calendar_name

        self.client = None
        self.calendar = None
        self.event_cache: dict[str, EventSnapshot] = {}
        self.sync_token: Optional[str] = None
        self.last_check: Optional[datetime] = None

        self._connect()

    def _connect(self):
        """Establish connection to CalDAV server"""
        self.client = caldav.DAVClient(
            url=self.CALDAV_URL,
            username=self.username,
            password=self.app_password
        )

        principal = self.client.principal()
        calendars = principal.calendars()

        if not calendars:
            raise ValueError("No calendars found")

        if self.calendar_name:
            for cal in calendars:
                if cal.name == self.calendar_name:
                    self.calendar = cal
                    break
            if not self.calendar:
                available = [c.name for c in calendars]
                raise ValueError(f"Calendar '{self.calendar_name}' not found. Available: {available}")
        else:
            self.calendar = calendars[0]

        print(f"Connected to calendar: {self.calendar.name}")

    def _get_etag(self, event) -> str:
        """Safely get etag from event"""
        # Try different ways to get etag
        if hasattr(event, 'etag') and event.etag:
            return event.etag
        if hasattr(event, 'get_property'):
            try:
                return event.get_property(dav.GetEtag()) or ""
            except:
                pass
        if hasattr(event, 'props') and event.props:
            for prop in event.props:
                if 'etag' in str(prop).lower():
                    return str(prop)
        # Fallback: hash the data
        if hasattr(event, 'data') and event.data:
            return hashlib.md5(event.data.encode()).hexdigest()
        return ""

    def _parse_event(self, event) -> Optional[EventSnapshot]:
        """Parse caldav event into EventSnapshot"""
        try:
            # Make sure we have the data
            if not hasattr(event, 'data') or not event.data:
                try:
                    event.load()
                except:
                    pass

            vevent = event.vobject_instance.vevent

            uid = str(vevent.uid.value) if hasattr(vevent, 'uid') else hashlib.md5(str(event.url).encode()).hexdigest()
            summary = str(vevent.summary.value) if hasattr(vevent, 'summary') else "No Title"

            start = None
            if hasattr(vevent, 'dtstart'):
                start = vevent.dtstart.value
                if not isinstance(start, datetime):
                    start = datetime.combine(start, datetime.min.time())

            end = None
            if hasattr(vevent, 'dtend'):
                end = vevent.dtend.value
                if not isinstance(end, datetime):
                    end = datetime.combine(end, datetime.min.time())

            last_modified = None
            if hasattr(vevent, 'last_modified'):
                last_modified = vevent.last_modified.value
            elif hasattr(vevent, 'dtstamp'):
                last_modified = vevent.dtstamp.value

            etag = self._get_etag(event)
            raw_data = event.data if hasattr(event, 'data') else ""

            return EventSnapshot(
                uid=uid,
                href=str(event.url),
                etag=etag,
                summary=summary,
                start=start,
                end=end,
                last_modified=last_modified,
                raw_data=raw_data
            )
        except Exception as e:
            print(f"Error parsing event: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_all_events(self, days_back: int = 30, days_forward: int = 365) -> list[EventSnapshot]:
        """Fetch all events within date range"""
        start = datetime.now() - timedelta(days=days_back)
        end = datetime.now() + timedelta(days=days_forward)

        snapshots = []

        # Method 1: Try search with date range
        try:
            events = self.calendar.search(
                start=start,
                end=end,
                event=True,
                expand=False
            )
        except Exception as e:
            print(f"Search failed, trying events(): {e}")
            # Method 2: Fallback to getting all events
            events = self.calendar.events()

        for event in events:
            # Ensure event data is loaded
            try:
                if not hasattr(event, 'data') or not event.data:
                    event.load()
            except Exception as e:
                print(f"Could not load event: {e}")
                continue

            snapshot = self._parse_event(event)
            if snapshot:
                snapshots.append(snapshot)

        return snapshots

    def check_changes(self) -> list[EventChange]:
        """
        Check for changes since last check.
        Returns list of EventChange objects.
        """
        changes = []
        now = datetime.now()

        current_events = self.get_all_events()
        current_by_uid = {e.uid: e for e in current_events}

        # Detect ADDED and MODIFIED
        for uid, current in current_by_uid.items():
            if uid not in self.event_cache:
                # New event
                changes.append(EventChange(
                    change_type=ChangeType.ADDED,
                    detected_at=now,
                    current=current,
                    previous=None
                ))
            else:
                previous = self.event_cache[uid]
                # Check if modified (etag changed or content changed)
                if previous.etag != current.etag or previous.raw_data != current.raw_data:
                    changes.append(EventChange(
                        change_type=ChangeType.MODIFIED,
                        detected_at=now,
                        current=current,
                        previous=previous
                    ))

        # Detect DELETED
        for uid, previous in self.event_cache.items():
            if uid not in current_by_uid:
                changes.append(EventChange(
                    change_type=ChangeType.DELETED,
                    detected_at=now,
                    current=None,
                    previous=previous
                ))

        # Update cache
        self.event_cache = current_by_uid
        self.last_check = now

        return changes

    def initialize_cache(self):
        """Initial population of event cache (no changes reported)"""
        events = self.get_all_events()
        self.event_cache = {e.uid: e for e in events}
        self.last_check = datetime.now()
        print(f"Initialized cache with {len(self.event_cache)} events")

    def watch(
            self,
            interval: int = 10,
            on_change: Optional[Callable[[list[EventChange]], None]] = None,
            on_error: Optional[Callable[[Exception], None]] = None,
            adaptive: bool = True
    ):
        """
        Start watching for changes.

        Args:
            interval: Base polling interval in seconds
            on_change: Callback for changes
            on_error: Callback for errors
            adaptive: If True, increase interval when no changes detected
        """
        print(f"Starting watch with {interval}s interval...")
        self.initialize_cache()

        current_interval = interval
        no_change_count = 0

        while True:
            try:
                changes = self.check_changes()

                if changes:
                    no_change_count = 0
                    current_interval = interval

                    print(f"\n{'=' * 50}")
                    print(f"Detected {len(changes)} change(s) at {datetime.now()}")
                    print('=' * 50)

                    for change in changes:
                        self._print_change(change)

                    if on_change:
                        on_change(changes)
                else:
                    no_change_count += 1
                    if adaptive and no_change_count > 10:
                        current_interval = min(interval * 3, 60)

                time.sleep(current_interval)

            except KeyboardInterrupt:
                print("\nStopping watcher...")
                break
            except Exception as e:
                print(f"Error: {e}")
                if on_error:
                    on_error(e)
                time.sleep(interval * 2)

    def _print_change(self, change: EventChange):
        """Pretty print a change"""
        if change.change_type == ChangeType.ADDED:
            print(f"\n🆕 ADDED: {change.current.summary}")
            print(f"   Start: {change.current.start}")
            print(f"   End: {change.current.end}")
            print(f"   UID: {change.current.uid}")

        elif change.change_type == ChangeType.DELETED:
            print(f"\n🗑️  DELETED: {change.previous.summary}")
            print(f"   Was scheduled: {change.previous.start}")
            print(f"   UID: {change.previous.uid}")
            print(f"   Last known state from: {change.previous.captured_at}")

        elif change.change_type == ChangeType.MODIFIED:
            print(f"\n✏️  MODIFIED: {change.current.summary}")
            print(f"   UID: {change.current.uid}")

            # Show what changed
            prev, curr = change.previous, change.current
            if prev.summary != curr.summary:
                print(f"   Title: '{prev.summary}' → '{curr.summary}'")
            if prev.start != curr.start:
                print(f"   Start: {prev.start} → {curr.start}")
            if prev.end != curr.end:
                print(f"   End: {prev.end} → {curr.end}")
            if prev.last_modified and curr.last_modified:
                print(f"   Modified at: {curr.last_modified}")


def default_change_handler(changes: list[EventChange]):
    """Example callback that saves changes to JSON"""
    data = [c.to_dict() for c in changes]

    with open("calendar_changes.json", "a") as f:
        for change in data:
            f.write(json.dumps(change) + "\n")


# ============== USAGE ==============

if __name__ == "__main__":
    # Create App-Specific Password at: https://appleid.apple.com/account/manage
    # Under "Sign-In and Security" → "App-Specific Passwords"

    CALENDAR_NAME = None  # None = first calendar, or specify name

    watcher = AppleCalendarWatcher(
        username=ICLOUD_EMAIL,
        app_password=APP_PASSWORD,
        calendar_name=CALENDAR_NAME
    )

    # Option 1: Just check once
    # watcher.initialize_cache()
    # changes = watcher.check_changes()
    # print(changes)

    # Option 2: Continuous watching
    watcher.watch(
        interval=10,  # Check every 10 seconds
        on_change=default_change_handler,  # Save to JSON
        adaptive=True  # Slow down if no changes
    )