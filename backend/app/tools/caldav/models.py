from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


@dataclass(slots=True)
class CalDavEvent:
    """In-memory representation of a CalDAV event.

    Designed to be easily convertible to/from iCalendar objects and persisted remotely.
    """

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    description: str | None = None
    start: datetime | None = None
    end: datetime | None = None
    rrule: Dict[str, Any] | None = None
    status: str | None = None  # needs-action, completed, cancelled
    remote_uid: str | None = None
    calendar_id: str | None = None
    user_id: int | None = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None
    sync_status: str | None = None  # e.g., synced, pending, conflicted

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)

    def mark_deleted(self) -> None:
        self.deleted_at = datetime.now(timezone.utc)
