import asyncio
import datetime
from uuid import uuid4
from types import SimpleNamespace

from aiocaldav import Calendar as AIOCalendar
from caldav import Calendar
from icalendar import Calendar as ICalCalendar
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.deps import async_get_db_cm
from server.db.models.caldav_events import CalDavEvent
from server.utils.utils import extract_uid
from server.app.core.logging_config import logger


class CalDavORM:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.client = None

        self.Calendar = self.Calendar(self)
        self.Event = self.Event(self)

    async def authenticate(self):
        from server.services.caldav.caldav_client import get_caldav_client

        self.client = await get_caldav_client(self.user_id)
        return self

        # Initializing inner ORM models
        self.Calendar = self.Calendar(self)
        self.Event = self.Event(self)


    # ========================
    # ==   CALENDAR MODEL   ==
    # ========================
    class Calendar:
        def __init__(self, orm):
            self.orm = orm  # ссылка на CalDavORM (для запросов и аутентификации)

        # --- CREATE ---
        async def create(self, title: str, **kwargs):
            """Create new calendar with specified title. Returns the created calendar object."""
            client = self.orm.client
            if not client:
                logger.error("Client not authenticated. Call orm.authenticate() first.")
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")

            def _create_calendar():
                principal = client.principal()
                new_cal = principal.make_calendar(name=title)
                return new_cal

            return await asyncio.to_thread(_create_calendar)

        # --- READ ---
        async def get(self, uid: str):
            """Get calendar by UID. Returns the calendar object if found, None otherwise."""
            client = self.orm.client
            if not client:
                logger.error("Client not authenticated. Call orm.authenticate() first.")
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")

            def _get_calendar():
                principal = client.principal()
                calendars = principal.calendars()

                for calendar in calendars:
                    if str(uid) in extract_uid(str(calendar.url)):
                        return calendar

                return None

            return await asyncio.to_thread(_get_calendar)

        # --- GET CALENDAR BY NAME ---
        async def get_by_name(self, name: str):
            """Get calendar by name. Returns the calendar object if found, None otherwise."""
            client = self.orm.client
            if not client:
                logger.error("Client not authenticated. Call orm.authenticate() first.")
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")

            def _get_calendar_by_name():
                principal = client.principal()
                calendars = principal.calendars()
                calendar = None
                for calendar in calendars:
                    print(calendar.name)
                    if calendar.name == name:
                        return calendar

                if calendar is None:
                    logger.warning(f"Calendar with name {name} not found.")
                if calendar:
                    return calendar

            return await asyncio.to_thread(_get_calendar_by_name)

        async def all(self):
            """
            Executes the retrieval of all calendars and returns their details as a list
            of dictionaries. Each dictionary includes the unique identifier (UID), name,
            and URL of the calendar.

            Raises
            ------
            RuntimeError
                If the client is not authenticated before invoking this method. Ensure
                to call `orm.authenticate()` before usage.

            Returns
            -------
            list of dict
                A list containing dictionaries, each representing a calendar. Every
                dictionary includes the following keys:
                    - uid (str): The unique identifier of the calendar, extracted from
                      the calendar URL.
                    - name (str or None): The name of the calendar, or None if not
                      specified.
                    - url (str or None): The URL of the calendar, or None if not
                      available.
            """
            client = self.orm.client
            if not client:
                logger.error("Client not authenticated. Call orm.authenticate() first.")
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")

            def _all_calendars():
                principal = client.principal()
                calendars = principal.calendars()

                result = []
                for cal in calendars:
                    url = getattr(cal, 'url', None)
                    result.append({
                        "uid": extract_uid(url),
                        "name": getattr(cal, 'name', None),
                        "url": getattr(cal, 'url', None),
                    })
                return result

            return await asyncio.to_thread(_all_calendars)

        # --- UPDATE ---
        async def update(self, uid: str, name: str):
            """
            Updates the name of a calendar identified by its UID.

            This asynchronous method updates the name of a calendar in the CalDAV server.
            The operation requires an authenticated client. If the client is not
            authenticated, an exception will be raised.

            Parameters
            ----------
            uid : str
                The unique identifier of the calendar to update.
            name : str
                The new name to assign to the calendar.

            Returns
            -------
            Calendar
                The updated calendar object.

            Raises
            ------
            RuntimeError
                If the client is not authenticated before invoking the method.
            ValueError
                If no calendar is found with the specified UID.

            """
            client = self.orm.client
            if not client:
                logger.error("Client not authenticated. Call orm.authenticate() first.")
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")

            def _update_name():
                principal = client.principal()
                calendar = None
                for cal in principal.calendars():
                    if str(uid) in str(cal.url):
                        calendar = cal
                        break

                if not calendar:
                    logger.warning(f"Calendar with UID {uid} not found.")
                    raise ValueError(f"Calendar with UID {uid} not found.")

                calendar.name = name
                calendar.save()
                return calendar

            updated_calendar = await asyncio.to_thread(_update_name)
            return updated_calendar

        # --- DELETE ---
        async def delete(self, calendar: Calendar):
            """
            Deletes a resource identified by the provided calendar object.

            This asynchronous method interacts with the ORM layer to delete a resource.
            The operation requires an authenticated client. If the client is not
            authenticated, an exception will be raised.

            Args:
                calendar: Calendar object to delete.

            Raises:
                RuntimeError: If the client is not authenticated before invoking the method.
            """
            client = self.orm.client
            if not client:
                logger.error("Client not authenticated. Call orm.authenticate() first.")
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")

            def _delete_calendar(calendar: Calendar):
                calendar.delete()
                return True

            return await asyncio.to_thread(_delete_calendar, calendar=calendar)

        # --- EXTRA ---
        async def get_events(self, uid: str):
            """Get all events for calendar with specified UID."""
            client = self.orm.client
            if not client:
                logger.error("Client not authenticated. Call orm.authenticate() first.")
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")
            pass

        async def create_event(self, uid: str, **kwargs):
            """Создать событие в этом календаре"""
            client = self.orm.client
            if not client:
                logger.error("Client not authenticated. Call orm.authenticate() first.")
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")
            pass


    # =====================
    # ==   EVENT MODEL   ==
    # =====================
    class Event:
        def __init__(self, orm):
            self.orm = orm

        async def create(self, calendar_uid: str, title: str, start: str, end: str, **kwargs):
            """
            Create a new event in the calendar.

            Parameters:
                calendar_uid: str - UID of the calendar to add the event to
                title: str - title of the event
                start: str - start datetime in ISO 8601 format
                end: str - end datetime in ISO 8601 format
                kwargs: dict - optional additional properties like description, location

            Returns:
                The created event object
            """
            client = self.orm.client
            if not client:
                logger.error("Client not authenticated. Call orm.authenticate() first.")
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")
            logger.info(f"Creating event in calendar {calendar_uid}")
            calendar = await self.orm.Calendar.get(uid=calendar_uid)
            if not calendar:
                raise ValueError(f"Calendar with UID {calendar_uid} not found.")

            def _create_event():
                from icalendar import Event, vDatetime

                event = Event()
                event.add("summary", title)
                event.add("dtstart", vDatetime(start))
                event.add("dtend", vDatetime(end))

                if "description" in kwargs:
                    event.add("description", kwargs["description"])
                if "location" in kwargs:
                    event.add("location", kwargs["location"])

                return calendar.add_event(event.to_ical())
            try:
                return await asyncio.to_thread(_create_event)
            except Exception as e:
                logger.error(f"Failed to create event: {e}")
                raise e
        # --- READ ---
        async def get(self, uid: str):
            """Получить одно событие по UID"""
            client = self.orm.client
            if not client:
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")
            calendar = await self.orm.Calendar.get(uid=uid)
            def _get_event(uid):
                if not calendar:
                    return None
                return calendar.get_event(uid)
            return await asyncio.to_thread(_get_event, uid=uid)

        async def all(self, calendar_uid: str):
            """Get all events from a CalDAV calendar, returning simple objects."""
            client = self.orm.client
            if not client:
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")

            calendar = await self.orm.Calendar.get(uid=calendar_uid)
            if not calendar:
                raise ValueError(f"Calendar with UID {calendar_uid} not found.")

            def _get_all_events(calendar):
                result = []

                try:
                    raw_events = calendar.events()
                except Exception:
                    try:
                        raw_events = calendar.get_events()
                    except Exception:
                        raw_events = []

                for ev in raw_events:
                    try:
                        # get ICS data
                        ics = getattr(ev, "data", None) or getattr(ev, "instance", None)
                        if ics and hasattr(ics, "to_ical"):
                            ics = ics.to_ical()
                        if isinstance(ics, bytes):
                            ics = ics.decode("utf-8", errors="ignore")
                        if not ics:
                            continue

                        cal = ICalCalendar.from_ical(ics)
                        for comp in cal.walk():
                            if comp.name == "VEVENT":
                                uid = str(comp.get("uid"))
                                url = getattr(ev, "url", None) or getattr(ev, "href", None)
                                title = str(comp.get("summary")) if comp.get("summary") else None
                                start = comp.get("dtstart").dt if comp.get("dtstart") else None
                                end = comp.get("dtend").dt if comp.get("dtend") else None
                                description = str(comp.get("description")) if comp.get("description") else None

                                result.append(SimpleNamespace(
                                    uid=uid,
                                    url=url,
                                    title=title,
                                    start=start,
                                    end=end,
                                    description=description,
                                    raw=ev,
                                ))
                                break
                    except Exception:
                        continue
                return result

            return await asyncio.to_thread(_get_all_events, calendar)

        # --- UPDATE ---
        async def update(self, uid: str, **kwargs):
            """Обновить событие"""
            client = self.orm.client
            if not client:
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")
            pass

        # --- DELETE ---
        async def delete(self, uid: str):
            """Удалить событие"""
            client = self.orm.client
            if not client:
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")
            pass

        # --- SAVE EVENTS TO DB ---

        async def save_from_caldav(self, calendar_uid: str, user_id):
            """Save events from CalDAV to the database."""
            client = self.orm.client
            if not client:
                logger.error("Client not authenticated. Call orm.authenticate() first.")
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")

            calendar = await self.orm.Calendar.get(uid=calendar_uid)
            if not calendar:
                logger.warning(f"Calendar with UID {calendar_uid} not found.")
                raise ValueError(f"Calendar with UID {calendar_uid} not found.")
            try:
                events = await self.orm.Event.all(calendar_uid)
            except Exception as e:
                logger.warning(f"Failed to get events from CalDAV: {e}")
                return
            try:
                for event in events:
                    # TODO: Here I need to parse the event and save it to the database
                    try:
                        uid = event.uid
                        url = event.url
                        title = event.title
                        start = event.start
                        end = event.end
                        description = event.description

                        logger.info(f"{title}")
                    except Exception as e:
                        logger.warning(f"Failed to parse event: {e}")
                        continue

                    await CalDavEvent.create(
                        user_id=user_id,
                        caldav_uid=uid,
                        title=title,
                        description=description,
                        start_date=start,
                        end_date=end,
                        last_modified_source="caldav"
                    )

            except Exception as e:
                logger.warning(f"Failed to get events: {e}")