from backend.app.db.database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    username: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(nullable=True)
    # id = Column(Integer, primary_key=True)
    # email = Column(String, unique=True, index=True)
    # username = Column(String, unique=True, index=True)
    # hashed_password = Column(String, nullable=False)
    # created_at = Column(DateTime, default=datetime.utcnow)
    # is_superuser = Column(Boolean, default=False)
    # is_active = Column(Boolean, default=True)
