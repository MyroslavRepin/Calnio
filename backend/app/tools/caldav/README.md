## CalDAV Async ORM (aiocaldav + icalendar)

This module provides a lightweight async ORM-like layer for working with CalDAV calendars using `aiocaldav` and `icalendar`.

- Event model: `CalDavEvent` (in-memory, easy to map to Pydantic)
- Async CRUD operations against CalDAV calendars
- iCalendar (.ics) generation/parsing, including RRULE
- Keyword search, status and interval filters
- Designed for integration in FastAPI services

### Requirements

Add to `requirements.txt` (already present in this repo):

```
aiocaldav
icalendar
```

### Module layout

- `models.py`: `CalDavEvent` dataclass with common event fields
- `orm.py`: `CalDavORM` async wrapper over aiocaldav client/calendar

### CalDavEvent fields

```text
id: UUID
title: str
description: str | None
start: datetime | None
end: datetime | None
rrule: dict | None  # e.g. {"FREQ": "DAILY"}
status: str | None  # needs-action, completed, cancelled
remote_uid: str | None
calendar_id: str | None
user_id: int | None
created_at: datetime (auto)
updated_at: datetime (auto)
deleted_at: datetime | None
sync_status: str | None
```

### CalDavORM methods

- `CalDavORM(client)`

  - `client`: aiocaldav `DAVClient`

- `await get_calendars() -> list[Any]`

  - Returns list of calendars for the authenticated principal

- `await create_event(calendar, event: CalDavEvent) -> str | None`

  - Creates a remote event. Returns `remote_uid` if successful

- `await get_event(calendar, uid: str) -> CalDavEvent | None`

  - Fetches and parses a remote event by UID

- `await update_event(calendar, uid: str, event: CalDavEvent) -> bool`

  - Updates the remote event by UID with data from `event`

- `await delete_event(calendar, uid: str) -> bool`

  - Deletes the remote event by UID

- `await get_all_event_ids(calendar) -> list[str]`

  - Returns all remote UIDs for events in a calendar

- `await get_events(calendar, start: datetime | None = None, end: datetime | None = None, filters: dict | None = None) -> list[CalDavEvent]`
  - Lists events; optional interval filter and `filters` such as:
    - `filters={"keywords": ["meeting", "daily"], "status": "completed", "rrule": {"FREQ": "DAILY"}}`

### Quick start

```python
from datetime import datetime, timezone, timedelta
from aiocaldav import DAVClient
from backend.app.tools.caldav.models import CalDavEvent
from backend.app.tools.caldav.orm import CalDavORM

client = DAVClient(url="https://caldav.example.com/", username="user", password="pass")
orm = CalDavORM(client)

principal = await client.principal()
calendars = await orm.get_calendars()
calendar = calendars[0]

# Create
event = CalDavEvent(
    title="Meeting",
    start=datetime(2025, 10, 7, 15, 0, tzinfo=timezone.utc),
    end=datetime(2025, 10, 7, 16, 0, tzinfo=timezone.utc),
    rrule={"FREQ": "DAILY"},
)
uid = await orm.create_event(calendar, event)

# List for a month
start = datetime.now(timezone.utc)
end = start + timedelta(days=30)
events = await orm.get_events(calendar, start=start, end=end)

# Update
event.title = "New Title"
await orm.update_event(calendar, uid, event)

# Delete
await orm.delete_event(calendar, uid)
```

### Advanced filtering examples

```python
# Keywords in title/description
events = await orm.get_events(calendar, filters={"keywords": ["standup", "retro"]})

# Status filtering
events = await orm.get_events(calendar, filters={"status": "completed"})

# RRULE exact match
events = await orm.get_events(calendar, filters={"rrule": {"FREQ": "WEEKLY", "BYDAY": ["MO"]}})

# Interval filter (overlap with window)
from datetime import timedelta
window_start = datetime.now(timezone.utc)
window_end = window_start + timedelta(days=7)
events = await orm.get_events(calendar, start=window_start, end=window_end)
```

### Notes

- The ORM tries common CalDAV methods: `date_search`, `events`, `items`. If missing, it falls back to raw `PUT/DELETE` via `calendar.client` and constructs an `.ics` href.
- RRULE is passed as a dict to `icalendar.Event.add("rrule", ...)`.
- This layer does not persist to a local database by itself; it is intended to be composed with your own persistence (SQLAlchemy/Pydantic models).
