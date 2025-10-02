# app/models/user_notion_integration.py

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Integer
from backend.db.database import Base
# from backend.app.models.users import User


class UserNotionIntegration(Base):
    __tablename__ = "notion_integrations"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False)

    access_token: Mapped[str] = mapped_column(nullable=False)
    refresh_token: Mapped[str] = mapped_column(nullable=False)

    workspace_id: Mapped[str] = mapped_column(nullable=False)
    workspace_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    bot_id: Mapped[Optional[str]] = mapped_column(nullable=True)
    notion_user_id: Mapped[Optional[str]] = mapped_column(nullable=True)
    duplicated_template_id: Mapped[Optional[str]
                                   ] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="notion_integration")
