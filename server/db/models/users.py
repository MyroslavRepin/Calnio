from server.db.database import Base
from sqlalchemy import Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(unique=True)
    icloud_email: Mapped[str] = mapped_column(unique=True, nullable=True)
    app_specific_password: Mapped[str] = mapped_column(nullable=True)
    username: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    notion_integration = relationship(
        "UserNotionIntegration", back_populates="user", uselist=False, lazy="selectin")

    notion_tasks = relationship(
        "UserNotionTask", back_populates="user", lazy="selectin")

    active_sync: Mapped[bool] = mapped_column(Boolean, default=False)

    # calendars = relationship(
    #     "UserCalendar", back_populates="user", uselist=True, lazy="selectin")
    caldav_events = relationship(
        "CalDavEvent", back_populates="user", lazy="selectin")
    
    caldav_calendar_name: Mapped[Optional[str]] = mapped_column(nullable=True)