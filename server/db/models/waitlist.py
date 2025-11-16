from server.db.database import Base
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

from server.db.models.enums import SyncStatus

class Waitlist(Base):
    """
    Represents a waitlist entity in the application.

    The Waitlist class models the attributes and behavior associated with a waiting list entry,
    including an identifier, user email, created timestamp, and discount eligibility. It is
    designed for storing individual waitlist entries in a database.

    Attributes:
        id: The unique identifier for the waitlist entry, which is auto-incremented.
        email: The email address of the individual associated with the waitlist entry.
        created_at: The timestamp marking when the waitlist entry was created.
        discount: A boolean flag indicating whether the individual is eligible for a discount.
    """
    __tablename__ = "waitlist"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    discount: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
