from typing import AsyncGenerator
from server.db.database import SessionLocal, AsyncSessionLocal
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession


async def async_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

@asynccontextmanager
async def async_get_db_cm() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
