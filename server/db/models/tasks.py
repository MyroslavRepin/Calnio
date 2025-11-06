from server.db.database import Base
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

from server.db.models.enums import SyncStatus


class UserNotionTask(Base):
    __tablename__ = "notion_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    notion_page_id: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    notion_url: Mapped[str] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    priority: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    select_option: Mapped[Optional[str]] = mapped_column(String, nullable=True)


    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Связь с пользователем
    user: Mapped["User"] = relationship("User", back_populates="notion_tasks")

    sync_source: Mapped[str] = mapped_column(String)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    caldav_id: Mapped[str] = mapped_column(String)
    has_conflict: Mapped[Boolean] = mapped_column(Boolean, default=False)
    last_modified_source: Mapped[str] = mapped_column(String)


    sync_status: Mapped[SyncStatus] = mapped_column(
        PGEnum(SyncStatus, name='syncstatus', native_enum=True),
        default=SyncStatus.pending,
        nullable=False
    )
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
