from server.db.database import Base
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship, Mapped, mapped_column


class Calendar(Base):
    __tablename__ = "calendars"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    uid: Mapped[str] = mapped_column(unique=True, nullable=False)
    url: Mapped[str] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    color: Mapped[str | None] = mapped_column(nullable=True)
    is_default: Mapped[bool] = mapped_column(default=False)
    external_service: Mapped[str | None] = mapped_column(nullable=True)

    # user: Mapped["User"] = relationship(back_populates="calendars")