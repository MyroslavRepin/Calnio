from server.db.database import Base
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

from server.db.models.enums import SyncStatus


class UserNotionTask(Base):
    """
        Represents a Notion task/page belonging to a user.

        Table: notion_tasks

        Fields:
        -------
        id : int
            Unique identifier for the task, primary key, auto-incremented.

        user_id : int
            Foreign key referencing the users table (users.id). Indicates the task owner.

        notion_page_id : str
            Unique identifier of the page in Notion. Can be NULL.

        notion_url : str
            URL link to the Notion page. Can be NULL.

        title : str
            Task/page title. Required field.

        description : Optional[str]
            Description of the task. Can be NULL.

        status : Optional[str]
            Task status, e.g., "new", "in progress", "done". Can be NULL.

        priority : Optional[str]
            Task priority, e.g., "high", "medium", "low". Can be NULL.

        select_option : Optional[str]
            Optional category or tag for the task. Can be NULL.

        start_date : Optional[datetime]
            Start date and time of the task. Can be NULL.

        end_date : Optional[datetime]
            End date and time of the task. Can be NULL.

        done : bool
            Completion flag for the task. Defaults to False.

        created_at : datetime
            Timestamp when the record was created. Set automatically.

        updated_at : datetime
            Timestamp when the record was last updated. Updated automatically on change.

        user : User
            ORM relationship to the User object.

        sync_source : str
            Source of task synchronization (e.g., Notion, CalDAV).

        last_synced_at : datetime
            Timestamp of the last successful synchronization. Updated automatically.

        caldav_id : str
            Optional ID used for CalDAV integration.

        has_conflict : bool
            Flag indicating if there is a sync conflict. Defaults to False.

        last_modified_source : str
            Tracks which source last modified this task.

        sync_status : SyncStatus
            Enum representing the sync status (e.g., pending, synced). Defaults to pending.

        deleted : bool
            Flag indicating if the task was deleted. Defaults to False.

        deleted_at : datetime
            Timestamp when the task was marked as deleted. Can be NULL.
        """

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
