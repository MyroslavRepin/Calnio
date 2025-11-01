import uuid
from time import timezone

from server.db.database import Base
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, ENUM as PGEnum


from server.db.deps import async_get_db_cm
from server.app.core.logging_config import logger
from server.db.models.enums import SyncStatus


class CalDavEvent(Base):
    __tablename__ = "caldav_events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    caldav_uid: Mapped[str] = mapped_column(String, unique=True)
    caldav_url: Mapped[str] = mapped_column(String, unique=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    user: Mapped["User"] = relationship("User", back_populates="caldav_events", lazy="selectin")

    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    has_conflict: Mapped[bool] = mapped_column(Boolean, default=False)
    last_modified_source: Optional[str] = "notion"

    notion_page_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sync_source: Mapped[str] = mapped_column(String)

    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    sync_status: Mapped[SyncStatus] = mapped_column(
        PGEnum(SyncStatus, name='syncstatus', native_enum=True),
        default=SyncStatus.pending,
        nullable=False
    )

    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)