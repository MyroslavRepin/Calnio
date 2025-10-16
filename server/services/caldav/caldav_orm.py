import asyncio
import datetime
from uuid import uuid4

from aiocaldav import Calendar as AIOCalendar
from caldav import Calendar

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
            """Создать новое событие в календаре"""
            client = self.orm.client
            if not client:
                logger.error("Client not authenticated. Call orm.authenticate() first.")
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")

            # Находим календарь
            calendars = await client.principal().calendars()
            calendar: Calendar = next((c for c in calendars if calendar_uid in c.url), None)
            if not calendar:
                logger.warning(f"Calendar with UID '{calendar_uid}' not found.")
                raise ValueError(f"Calendar with UID '{calendar_uid}' not found.")

            # Формируем контент события (iCalendar)
            event_uid = str(uuid4())
            dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            dtstart = datetime.fromisoformat(start).strftime("%Y%m%dT%H%M%SZ")
            dtend = datetime.fromisoformat(end).strftime("%Y%m%dT%H%M%SZ")

            description = kwargs.get("description", "")
            location = kwargs.get("location", "")

            ics_content = f"""BEGIN:VCALENDAR
    VERSION:2.0
    PRODID:-//Calnio//CalDavORM//EN
    BEGIN:VEVENT
    UID:{event_uid}
    DTSTAMP:{dtstamp}
    DTSTART:{dtstart}
    DTEND:{dtend}
    SUMMARY:{title}
    DESCRIPTION:{description}
    LOCATION:{location}
    END:VEVENT
    END:VCALENDAR
    """

            # Загружаем событие в календарь (в отдельном потоке)
            new_event = await asyncio.to_thread(calendar.add_event, ics_content)

            return {
                "uid": event_uid,
                "title": title,
                "start": start,
                "end": end,
                "calendar": calendar_uid,
                "created": True
                }
        # --- READ ---
        async def get(self, uid: str):
            """Получить одно событие по UID"""
            client = self.orm.client
            if not client:
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")
            pass

        async def all(self, calendar_uid: str):
            """Получить все события из календаря"""
            client = self.orm.client
            if not client:
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")
            pass

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
