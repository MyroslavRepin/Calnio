from backend.app.db.base_class import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_superuser = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
