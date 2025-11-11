from server.db.database import Base
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, func, Integer, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

class UserNotionTask(Base):
    __tablename__ = "notion_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    notion_page_id: Mapped[str] = mapped_column(String)
    notion_url: Mapped[str] = mapped_column(String, nullable=False)
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

    user: Mapped["User"] = relationship(back_populates="notion_tasks")

    sync_source: Mapped[str] = mapped_column(String)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    caldav_id: Mapped[str] = mapped_column(String)
    has_conflict: Mapped[Boolean] = mapped_column(Boolean, default=False)
    last_modified_source: Mapped[str] = mapped_column(String)

    __table_args__ = (
        UniqueConstraint('user_id', 'notion_page_id', name='uq_user_notion_page'),
    )

