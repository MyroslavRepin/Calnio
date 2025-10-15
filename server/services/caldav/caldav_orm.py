import asyncio
import datetime
from uuid import uuid4

from aiocaldav import Calendar

from server.utils.utils import extract_uid


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
            """Создать новый календарь"""
            client = self.orm.client
            if not client:
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")
            pass

        # --- READ ---
        async def get(self, uid: str):
            """Получить календарь по UID"""
            client = self.orm.client
            if not client:
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")
            pass


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
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")
            principal = await client.principal()
            calendars = await principal.calendars()
            result = []
            for cal in calendars:
                url = getattr(cal, 'url', None)
                result.append({
                    "uid": extract_uid(url),
                    "name": getattr(cal, 'name', None),
                    "url": getattr(cal, 'url', None),
                })
            return result

        # --- UPDATE ---
        async def update(self, uid: str, **kwargs):
            """Обновить календарь (название, цвет, и т.п.)"""
            client = self.orm.client
            if not client:
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")
            pass

        # --- DELETE ---
        async def delete(self, uid: str):
            """Удалить календарь"""
            client = self.orm.client
            if not client:
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")
            pass

        # --- EXTRA ---
        async def get_events(self, uid: str):
            """Получить все события календаря"""
            client = self.orm.client
            if not client:
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")
            pass

        async def create_event(self, uid: str, **kwargs):
            """Создать событие в этом календаре"""
            client = self.orm.client
            if not client:
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
                raise RuntimeError("Client not authenticated. Call orm.authenticate() first.")

            # Находим календарь
            calendars = await client.principal().calendars()
            calendar: Calendar = next((c for c in calendars if calendar_uid in c.url), None)
            if not calendar:
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
