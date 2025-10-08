from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from icalendar import Calendar as ICalCalendar, Event as ICalEvent

from .models import CalDavEvent


try:
    from loguru import logger
except Exception:  # pragma: no cover
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


class CalDavORM:
    """Async ORM-like helper over aiocaldav client/calendar objects.

    This class does not persist local state by itself; it focuses on converting
    between `CalDavEvent` and iCalendar, and interacting with a CalDAV server
    via aiocaldav Calendar/DAVClient-like APIs.
    """

    def __init__(self, client: Any) -> None:
        self.client = client

    # ---------- Public API ----------
    async def get_calendars(self) -> list[Any]:
        """Return list of calendars for the authenticated user."""
        try:
            principal = await self.client.principal()
            calendars = await principal.calendars()
            return list(calendars)
        except Exception as exc:  # pragma: no cover
            logger.exception("Failed to fetch calendars: {}", exc)
            return []

    async def create_event(self, calendar: Any, event: CalDavEvent) -> str | None:
        """Create event remotely, return remote UID on success."""
        try:
            ics_bytes = self._build_ics(event)
            # Prefer calendar.add_event if available, else raw PUT
            if hasattr(calendar, "add_event"):
                created = await calendar.add_event(ics_bytes)
                uid = self._extract_uid_from_created(
                    created) or event.remote_uid
            else:
                # Fallback path: generate a path from UID
                uid = event.remote_uid or self._generate_uid()
                href = self._build_href(calendar, uid)
                await calendar.client.put(href, ics_bytes, headers={"Content-Type": "text/calendar"})
            logger.info("Created CalDAV event uid={} title={}.",
                        uid, event.title)
            return uid
        except Exception as exc:  # pragma: no cover
            logger.exception("Failed to create event: {}", exc)
            return None

    async def get_event(self, calendar: Any, uid: str) -> Optional[CalDavEvent]:
        try:
            ics = await self._fetch_ics_by_uid(calendar, uid)
            if not ics:
                return None
            return self._from_ics(ics, calendar_id=self._calendar_id(calendar))
        except Exception as exc:  # pragma: no cover
            logger.exception("Failed to get event {}: {}", uid, exc)
            return None

    async def update_event(self, calendar: Any, uid: str, event: CalDavEvent) -> bool:
        try:
            event.remote_uid = uid
            event.touch()
            ics_bytes = self._build_ics(event)
            href = self._build_href(calendar, uid)
            await calendar.client.put(href, ics_bytes, headers={"Content-Type": "text/calendar"})
            logger.info("Updated CalDAV event uid={} title={}.",
                        uid, event.title)
            return True
        except Exception as exc:  # pragma: no cover
            logger.exception("Failed to update event {}: {}", uid, exc)
            return False

    async def delete_event(self, calendar: Any, uid: str) -> bool:
        try:
            href = self._build_href(calendar, uid)
            await calendar.client.delete(href)
            logger.info("Deleted CalDAV event uid={}", uid)
            return True
        except Exception as exc:  # pragma: no cover
            logger.exception("Failed to delete event {}: {}", uid, exc)
            return False

    async def get_all_event_ids(self, calendar: Any) -> list[str]:
        try:
            events = await self._list_calendar_events(calendar)
            uids: list[str] = []
            for ev in events:
                try:
                    ics = await self._fetch_item_ics(ev)
                    uid = self._peek_uid(ics)
                    if uid:
                        uids.append(uid)
                except Exception:  # pragma: no cover
                    logger.exception(
                        "Failed to decode event while listing UIDs")
            return uids
        except Exception as exc:  # pragma: no cover
            logger.exception("Failed to list event ids: {}", exc)
            return []

    async def get_events(
        self,
        calendar: Any,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> list[CalDavEvent]:
        """Return events optionally filtered by time range, keywords, status, and rrule."""
        filters = filters or {}
        keywords: list[str] = [kw.lower()
                               for kw in filters.get("keywords", [])]
        status_filter: Optional[str] = filters.get("status")
        rrule_filter: Optional[dict] = filters.get("rrule")

        try:
            raw_items = await self._list_calendar_events(calendar, start=start, end=end)
            results: list[CalDavEvent] = []

            async def to_event(item: Any) -> Optional[CalDavEvent]:
                try:
                    ics = await self._fetch_item_ics(item)
                    model = self._from_ics(
                        ics, calendar_id=self._calendar_id(calendar))
                    return model
                except Exception:
                    logger.exception("Failed to decode ICS event")
                    return None

            # Fetch ICS bodies concurrently for speed
            tasks = [to_event(item) for item in raw_items]
            decoded: list[Optional[CalDavEvent]] = await asyncio.gather(*tasks)
            for ev in decoded:
                if ev is None:
                    continue
                # Local interval filtering: include events that overlap [start, end]
                if start or end:
                    s = ev.start
                    e = ev.end
                    if s is None and e is None:
                        # If no times, exclude when interval filter is present
                        continue
                    interval_start = start or s
                    interval_end = end or e
                    if interval_start and e and e < interval_start:
                        continue
                    if interval_end and s and s > interval_end:
                        continue

                if keywords:
                    text = f"{ev.title} {ev.description or ''}".lower()
                    if not any(kw in text for kw in keywords):
                        continue
                if status_filter and ev.status != status_filter:
                    continue
                if rrule_filter and (ev.rrule or {}) != rrule_filter:
                    continue
                results.append(ev)
            return results
        except Exception as exc:  # pragma: no cover
            logger.exception("Failed to list events: {}", exc)
            return []

    # ---------- iCalendar helpers ----------
    def _build_ics(self, event: CalDavEvent) -> bytes:
        cal = ICalCalendar()
        cal.add("prodid", "-//Calnio CalDAV ORM//EN")
        cal.add("version", "2.0")

        ev = ICalEvent()
        uid = event.remote_uid or self._generate_uid()
        ev.add("uid", uid)
        if event.title:
            ev.add("summary", event.title)
        if event.description:
            ev.add("description", event.description)
        if event.start:
            ev.add("dtstart", event.start)
        if event.end:
            ev.add("dtend", event.end)
        if event.status:
            ev.add("status", event.status.upper())
        if event.rrule:
            ev.add("rrule", event.rrule)

        cal.add_component(ev)
        ics = cal.to_ical()
        return ics if isinstance(ics, (bytes, bytearray)) else bytes(ics)

    def _from_ics(self, ics: bytes | str, calendar_id: Optional[str] = None) -> CalDavEvent:
        if isinstance(ics, str):
            ics = ics.encode("utf-8")
        cal = ICalCalendar.from_ical(ics)
        for component in cal.walk():
            if component.name == "VEVENT":
                remote_uid = str(component.get(
                    "uid")) if component.get("uid") else None
                title = str(component.get("summary") or "")
                description = str(component.get("description") or "") or None
                dtstart = component.get("dtstart")
                dtend = component.get("dtend")
                status_raw = component.get("status")
                rrule = component.get("rrule")

                start_dt = self._unwrap_dt(dtstart)
                end_dt = self._unwrap_dt(dtend)
                status = str(status_raw).lower() if status_raw else None

                return CalDavEvent(
                    title=title,
                    description=description,
                    start=start_dt,
                    end=end_dt,
                    rrule=dict(rrule) if rrule else None,
                    status=status,
                    remote_uid=remote_uid,
                    calendar_id=calendar_id,
                )
        raise ValueError("No VEVENT found in ICS")

    def _peek_uid(self, ics: bytes | str) -> Optional[str]:
        try:
            ev = self._from_ics(ics)
            return ev.remote_uid
        except Exception:
            return None

    # ---------- CalDAV helpers ----------
    async def _list_calendar_events(
        self, calendar: Any, start: Optional[datetime] = None, end: Optional[datetime] = None
    ) -> Iterable[Any]:
        # Try commonly available methods across CalDAV servers/clients
        if start or end:
            if hasattr(calendar, "date_search"):
                return await calendar.date_search(start, end)
        if hasattr(calendar, "events"):
            return await calendar.events()
        if hasattr(calendar, "items"):
            return await calendar.items()
        # Fallback: try a PROPFIND if exposed via client (not standard in aiocaldav)
        return []

    async def _fetch_item_ics(self, item: Any) -> bytes:
        # Commonly, items expose .data or .href to fetch content
        if hasattr(item, "data") and item.data is not None:
            data = item.data
            return data if isinstance(data, (bytes, bytearray)) else bytes(data)
        if hasattr(item, "href"):
            resp = await item.client.get(item.href)
            return resp
        # Last resort: try .ical
        if hasattr(item, "ical"):
            ics = await item.ical()
            return ics if isinstance(ics, (bytes, bytearray)) else bytes(ics)
        raise ValueError("Unsupported calendar item type; cannot fetch ICS")

    async def _fetch_ics_by_uid(self, calendar: Any, uid: str) -> Optional[bytes]:
        # Standard CalDAV does not require servers to support lookup by UID via API;
        # we iterate items and match UID client-side.
        items = await self._list_calendar_events(calendar)
        for it in items:
            try:
                ics = await self._fetch_item_ics(it)
                if self._peek_uid(ics) == uid:
                    return ics
            except Exception:
                continue
        return None

    def _build_href(self, calendar: Any, uid: str) -> str:
        base: str = getattr(calendar, "url", None) or getattr(
            calendar, "path", "")
        if not base.endswith("/"):
            base += "/"
        return f"{base}{uid}.ics"

    def _extract_uid_from_created(self, created_obj: Any) -> Optional[str]:
        # Some libraries return an object with .href or .data; extract UID by parsing ICS
        if hasattr(created_obj, "data") and created_obj.data:
            return self._peek_uid(created_obj.data)
        if hasattr(created_obj, "href") and created_obj.href:
            href: str = created_obj.href
            if href.endswith(".ics"):
                return href.split("/")[-1].removesuffix(".ics")
        return None

    def _calendar_id(self, calendar: Any) -> Optional[str]:
        return getattr(calendar, "url", None) or getattr(calendar, "path", None)

    # ---------- misc ----------
    def _generate_uid(self) -> str:
        # RFC5545 UIDs are arbitrary strings; use ISO timestamp + domain-like suffix
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        return f"{ts}-calnio@local"

    @staticmethod
    def _unwrap_dt(value: Any) -> Optional[datetime]:
        if not value:
            return None
        # icalendar may wrap in vDDDTypes; attempt to access .dt
        dt = getattr(value, "dt", value)
        if isinstance(dt, datetime):
            # Normalize to aware UTC if naive
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        return None
