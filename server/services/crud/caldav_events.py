import uuid
from datetime import datetime, timedelta, timezone, date
from typing import List, Optional

import recurring_ical_events
from icalendar import Calendar as ICalCalendar, Event as ICalEvent, Todo

from server.app.core.logging_config import logger
from server.app.schemas.caldav_events import CalDavEventModel


# NOTE: We work with aiocaldav Calendar-like objects. Different servers/libraries expose
# slightly different methods (events, items, date_search, add_event, etc.).
# The helpers below try multiple options to stay compatible.


async def _list_calendar_items(calendar) -> list:
    """Return a list of calendar items (event resources) for a given calendar.

    Tries common aiocaldav APIs in order: events(), items().
    """
    for method in ("events", "items"):
        if hasattr(calendar, method):
            res = await getattr(calendar, method)()
            return res or []
    logger.warning("Calendar object has neither events() nor items(); returning empty list")
    return []


async def _date_search(calendar, start: datetime, end: datetime) -> list:
    """Try to fetch items by date range if the API supports it; otherwise fall back to listing all."""
    if hasattr(calendar, "date_search"):
        try:
            return await calendar.date_search(start, end)  # type: ignore[attr-defined]
        except Exception as e:
            logger.debug(f"date_search failed, falling back to full list: {e}")
    return await _list_calendar_items(calendar)


async def _get_item_data(item) -> bytes:
    """Return ICS data for an item as bytes, awaiting if necessary."""
    try:
        data = item.data
        if isinstance(data, (bytes, str)):
            return data if isinstance(data, bytes) else data.encode()
        # if coroutine
        data = await data
        return data if isinstance(data, bytes) else str(data).encode()
    except Exception:
        # Try to read via get or read method
        for attr in ("get", "read"):
            if hasattr(item, attr):
                res = await getattr(item, attr)()
                return res if isinstance(res, bytes) else str(res).encode()
        raise


def _icalendar_build_vcalendar_from_model(model: CalDavEventModel, as_todo: bool = False) -> bytes:
    """Build an ICS payload (bytes) from a CalDavEventModel."""
    vcal = ICalCalendar()
    vcal.add("prodid", "-//Calnio//EN")
    vcal.add("version", "2.0")

    if as_todo:
        comp = Todo()
        comp.add("summary", model.title)
        if model.start_date:
            comp.add("dtstart", model.start_date)
        if model.end_date:
            comp.add("due", model.end_date)
        if model.status:
            comp.add("status", model.status)
    else:
        comp = ICalEvent()
        comp.add("summary", model.title)
        if model.start_date:
            comp.add("dtstart", model.start_date)
        if model.end_date:
            comp.add("dtend", model.end_date)
        if model.status:
            comp.add("status", model.status)

    comp.add("uid", model.uid)
    comp.add("dtstamp", datetime.now(timezone.utc))
    vcal.add_component(comp)
    return vcal.to_ical()


def _parse_first_component_to_model(raw_ics: bytes) -> Optional[CalDavEventModel]:
    try:
        cal = ICalCalendar.from_ical(raw_ics)
    except Exception as e:
        logger.warning(f"Failed to parse ICS: {e}")
        return None

    for component in cal.walk():
        if component.name in ("VEVENT", "VTODO"):
            return CalDavEventModel(
                uid=str(component.get("UID")),
                title=str(component.get("SUMMARY", "Untitled")),
                start_date=getattr(component.get("DTSTART"), "dt", None),
                end_date=(getattr(component.get("DTEND"), "dt", None) if component.get("DTEND") else None),
                status=(str(component.get("STATUS")) if component.get("STATUS") else None),
                url=None,  # Might be filled by caller if known
            )
    return None


def _to_aware_datetime(value) -> Optional[datetime]:
    """Convert a date or naive datetime to an aware datetime (UTC)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)
    return None


class CalDavEvent:
    """A thin wrapper over a CalDAV item with a typed model and CRUD helpers."""

    def __init__(self, calendar, model: CalDavEventModel, url: Optional[str] = None, item=None):
        self.calendar = calendar
        self.model = model
        # item resource url (if known)
        self.url = url or getattr(item, "url", None)
        self._item = item

    @classmethod
    async def from_item(cls, calendar, item):
        raw_data = await _get_item_data(item)
        model = _parse_first_component_to_model(raw_data)
        if not model:
            return None
        model.url = str(getattr(item, "url", "")) or None
        return cls(calendar, model, url=model.url, item=item)

    def to_ics(self, as_todo: bool = False) -> bytes:
        return _icalendar_build_vcalendar_from_model(self.model, as_todo=as_todo)

    def to_dict(self) -> dict:
        return {
            "uid": self.model.uid,
            "title": self.model.title,
            "start_date": self.model.start_date,
            "end_date": self.model.end_date,
            "status": self.model.status,
            "url": self.url or self.model.url,
        }

    async def save(self, as_todo: bool = False):
        """Create or update the event on the server."""
        ics_data = self.to_ics(as_todo=as_todo)

        # Prefer calendar.add_event for create/update if available
        if hasattr(self.calendar, "add_event") and not self.url:
            try:
                created = await self.calendar.add_event(ics_data)  # type: ignore[attr-defined]
                self.url = str(getattr(created, "url", None) or self.url)
                self._item = created
                return
            except Exception as e:
                logger.debug(f"calendar.add_event failed, will try PUT: {e}")

        # If we know the url, PUT to it, otherwise create a new resource
        target_url = self.url or f"{self.calendar.url}/{self.model.uid}.ics"

        # Attempt to PUT via calendar.client if present
        client = getattr(self.calendar, "client", None)
        if client and hasattr(client, "put"):
            await client.put(target_url, ics_data)
            return

        # Try item update if available
        if self._item is not None:
            for attr in ("set_data", "save", "update"):
                if hasattr(self._item, attr):
                    try:
                        # Prefer set_data if present
                        if attr == "set_data":
                            await getattr(self._item, attr)(ics_data)
                        else:
                            await getattr(self._item, attr)(ics_data)
                        return
                    except Exception:
                        pass

        raise RuntimeError("No supported method to save CalDAV event for this calendar implementation")

    async def delete(self):
        """Delete the event from the server."""
        # If the item exposes delete
        if self._item is not None and hasattr(self._item, "delete"):
            await self._item.delete()
            return

        # Fallback: HTTP DELETE if client exists and url is known
        client = getattr(self.calendar, "client", None)
        if client and hasattr(client, "delete") and self.url:
            await client.delete(self.url)
            return

        raise RuntimeError("No supported method to delete CalDAV event for this calendar implementation")


# ---------- High-level helpers (CRUD and listing) ----------

async def get_all_events(calendar, months: int = 1) -> List[CalDavEvent]:
    """Fetch all VEVENT/VTODO items within ±months window and return CalDavEvent wrappers."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=30 * months)
    end = now + timedelta(days=30 * months)
    return await get_events_between(calendar, start, end)


async def get_events_between(calendar, start: datetime, end: datetime) -> List[CalDavEvent]:
    items = await _date_search(calendar, start, end)
    events: List[CalDavEvent] = []

    for item in items:
        try:
            raw_ics = await _get_item_data(item)
            try:
                # Expand recurring when possible; fallback to all comps
                cal = ICalCalendar.from_ical(raw_ics)
                try:
                    expanded = recurring_ical_events.of(cal).between(start, end)
                except Exception:
                    expanded = cal.walk()

                for comp in expanded:
                    if comp.name not in {"VTODO", "VEVENT"}:
                        continue
                    # Choose dates depending on component type
                    comp_dtstart = getattr(comp.get("DTSTART"), "dt", None)
                    comp_dtend = getattr(comp.get("DTEND"), "dt", None) if comp.get("DTEND") else None
                    comp_due = getattr(comp.get("DUE"), "dt", None) if comp.get("DUE") else None

                    start_dt_raw = comp_dtstart or (comp_due if comp.name == "VTODO" else None)
                    end_dt_raw = comp_dtend or (comp_due if comp.name == "VTODO" else None)

                    start_dt = _to_aware_datetime(start_dt_raw)
                    end_dt = _to_aware_datetime(end_dt_raw)

                    model = CalDavEventModel(
                        uid=str(comp.get("UID") or uuid.uuid4()),
                        title=str(comp.get("SUMMARY", "Untitled")),
                        start_date=start_dt,
                        end_date=end_dt,
                        status=(str(comp.get("STATUS")) if comp.get("STATUS") else None),
                        url=str(getattr(item, "url", "")) or None,
                    )

                    if start_dt and start <= start_dt <= end:
                        events.append(CalDavEvent(calendar, model, url=model.url, item=item))
            except Exception as e:
                logger.debug(f"ICS parse failed for an item: {e}")
                # Fallback to simpler parse
                model = _parse_first_component_to_model(raw_ics)
                if model:
                    model.url = str(getattr(item, "url", "")) or None
                    dt = _to_aware_datetime(model.start_date)
                    if not dt or not (start <= dt <= end):
                        # If VTODO w/o DTSTART, consider DUE via reparsing fields not exposed by simplified model
                        pass
                    events.append(CalDavEvent(calendar, model, url=model.url, item=item))
        except Exception as e:
            logger.warning(f"Failed to read calendar item: {e}")

    logger.info(f"Found {len(events)} events/tasks between {start} and {end}")
    return events


async def get_all_events_ids(calendar, months: int = 12) -> List[str]:
    """Return a list of UIDs for events in a wide range (default: ±12 months)."""
    events = await get_all_events(calendar, months=months)
    ids = []
    for ev in events:
        if ev.model.uid:
            ids.append(ev.model.uid)
    # Deduplicate while preserving order
    seen = set()
    result = []
    for uid in ids:
        if uid not in seen:
            seen.add(uid)
            result.append(uid)
    return result


async def get_event_by_uid(calendar, uid: str, months: int = 24) -> Optional[CalDavEvent]:
    """Fetch a single event by UID by scanning items (CalDAV servers often need search)."""
    if not uid:
        return None

    # Try broader window to increase likelihood
    events = await get_all_events(calendar, months=months)
    for ev in events:
        if ev.model.uid == uid:
            return ev
    return None


async def get_event_by_url(calendar, url: str, months: int = 24) -> Optional[CalDavEvent]:
    if not url:
        return None

    # Try direct match via listed items first
    items = await _list_calendar_items(calendar)
    for item in items:
        if str(getattr(item, "url", "")) == url:
            return await CalDavEvent.from_item(calendar, item)

    # Fallback: scan in a window to parse and match URL field
    events = await get_all_events(calendar, months=months)
    for ev in events:
        if (ev.url or ev.model.url) == url:
            return ev
    return None


async def create_event(calendar, title: str, start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None, status: Optional[str] = None,
                       as_todo: bool = False, uid: Optional[str] = None) -> CalDavEvent:
    model = CalDavEventModel(
        uid=uid or str(uuid.uuid4()),
        title=title,
        start_date=start_date,
        end_date=end_date,
        status=status,
        url=None,
    )
    ev = CalDavEvent(calendar, model)
    await ev.save(as_todo=as_todo)
    logger.info(f"Created CalDAV {'VTODO' if as_todo else 'VEVENT'}: {model.title} ({model.uid})")
    return ev


async def upsert_event(calendar, model: CalDavEventModel, as_todo: bool = False) -> CalDavEvent:
    existing = await get_event_by_uid(calendar, model.uid)
    if existing:
        existing.model.title = model.title
        existing.model.start_date = model.start_date
        existing.model.end_date = model.end_date
        existing.model.status = model.status
        await existing.save(as_todo=as_todo)
        logger.info(f"Upsert: updated {model.uid}")
        return existing
    ev = CalDavEvent(calendar, model)
    await ev.save(as_todo=as_todo)
    logger.info(f"Upsert: created {model.uid}")
    return ev


async def update_event(calendar, uid: str, *,
                       title: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       status: Optional[str] = None,
                       as_todo: Optional[bool] = None) -> Optional[CalDavEvent]:
    ev = await get_event_by_uid(calendar, uid)
    if not ev:
        logger.warning(f"Event with UID {uid} not found for update")
        return None

    if title is not None:
        ev.model.title = title
    if start_date is not None:
        ev.model.start_date = start_date
    if end_date is not None:
        ev.model.end_date = end_date
    if status is not None:
        ev.model.status = status

    await ev.save(as_todo=bool(as_todo)) if as_todo is not None else await ev.save()
    logger.info(f"Updated CalDAV event {uid}")
    return ev


async def mark_todo_completed(calendar, uid: str) -> Optional[CalDavEvent]:
    ev = await get_event_by_uid(calendar, uid)
    if not ev:
        logger.warning(f"Todo {uid} not found")
        return None
    ev.model.status = "COMPLETED"
    await ev.save(as_todo=True)
    logger.info(f"Marked todo {uid} as COMPLETED")
    return ev


async def delete_event_by_uid(calendar, uid: str) -> bool:
    ev = await get_event_by_uid(calendar, uid)
    if not ev:
        logger.warning(f"Event with UID {uid} not found for delete")
        return False
    await ev.delete()
    logger.info(f"Deleted CalDAV event {uid}")
    return True


async def delete_event_by_url(calendar, url: str) -> bool:
    if not url:
        return False

    # Try to identify item by url for proper delete if supported
    items = await _list_calendar_items(calendar)
    for item in items:
        if str(getattr(item, "url", "")) == url and hasattr(item, "delete"):
            await item.delete()
            logger.info(f"Deleted CalDAV item by url {url}")
            return True

    # Fallback: client.delete
    client = getattr(calendar, "client", None)
    if client and hasattr(client, "delete"):
        await client.delete(url)
        logger.info(f"Deleted CalDAV item by url {url} via client.delete")
        return True

    logger.warning("No method to delete by URL on this calendar")
    return False


# ---------- Existing function, slightly hardened ----------

async def get_caldav_tasks(calendar, months: int = 1):
    """
    Получает все задачи (VTODO и VEVENT) из календаря за указанный интервал (по умолчанию ±1 месяц).
    """

    try:
        logger.info(f"📆 Fetching tasks from calendar '{getattr(calendar, 'name', 'Unnamed')}'...")

        now = datetime.now(timezone.utc)
        start = now - timedelta(days=30 * months)
        end = now + timedelta(days=30 * months)

        # Получаем все элементы календаря
        items = await _date_search(calendar, start, end)
        tasks = []

        for item in items:
            try:
                raw_data = await _get_item_data(item)
                cal = ICalCalendar.from_ical(raw_data)
            except Exception as e:
                logger.warning(f"⚠️  Failed to parse calendar item: {e}")
                continue

            # Разворачиваем повторяющиеся события, если есть
            try:
                expanded_events = recurring_ical_events.of(cal).between(start, end)
            except Exception:
                expanded_events = cal.walk()

            for component in expanded_events:
                if component.name not in {"VTODO", "VEVENT"}:
                    continue

                summary = str(component.get("SUMMARY", "Untitled"))
                dtstart = component.get("DTSTART")
                due = component.get("DUE")
                # prefer DUE for VTODO when DTSTART missing
                raw_dt = getattr(dtstart, "dt", None) if dtstart else (getattr(due, "dt", None) if component.name == "VTODO" else None)
                dt = _to_aware_datetime(raw_dt)

                if not dt:
                    continue
                if not (start <= dt <= end):
                    continue

                tasks.append({
                    "summary": summary,
                    "type": component.name,
                    "start": dt,
                    "due": getattr(due, "dt", None) if due else None,
                    "status": str(component.get("STATUS", "NEEDS-ACTION")),
                    "uid": str(component.get("UID", uuid.uuid4())),
                })

        logger.info(f"✅ Found {len(tasks)} tasks/events in the interval ±{months} month(s).")
        return tasks

    except Exception as e:
        logger.error(f"❌ Error fetching CalDAV tasks: {e}")
        return []
