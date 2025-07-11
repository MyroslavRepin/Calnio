from typing import Annotated
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import MetaData, String, create_engine
from backend.app.core.config import settings

engine = create_engine(settings.database_url, echo=True)

SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False)

str_256 = Annotated[str, 256]


class Base(DeclarativeBase):
    type_annotation_map = {
        str_256: String(256)
    }
