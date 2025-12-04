from .users import User
from .tasks import UserNotionTask
from .notion_integration import UserNotionIntegration
from .caldav_events import CalDavEvent
from .calendars import Calendar
from .waitlist import Waitlist
from .enums import SyncStatus

# Provide legacy/expected aliases used elsewhere in the codebase
UserCalendar = Calendar
WaitlistEntry = Waitlist

__all__ = [
    "User",
    "UserNotionTask",
    "UserNotionIntegration",
    "CalDavEvent",
    "UserCalendar",
    "WaitlistEntry",
    "SyncStatus",
]
