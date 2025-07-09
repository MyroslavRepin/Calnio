from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://myroslav:myroslav0818@localhost:5432/scheduloo"

sync_engine = create_engine(DATABASE_URL, echo=True)

session_factory = sessionmaker(
    bind=sync_engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


metadata_obj = Base.metadata
