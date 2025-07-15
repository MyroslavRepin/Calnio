from typing import AsyncGenerator
from backend.app.db.database import SessionLocal, AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession


async def async_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
