from typing import AsyncGenerator
from server.db.database import AsyncSessionLocal
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides an asynchronous generator to yield a database session for interaction.

    The `get_db` function is a dependency function often used in asynchronous web
    applications to provide a database session to various routes or operations.
    It uses a context manager to ensure that the session is properly initialized
    and closed after use, maintaining the integrity and lifecycle of the session.

    :yield: An asynchronous session used to perform database interactions.
    :rtype: AsyncGenerator[AsyncSession, None]
    """
    async with AsyncSessionLocal() as session:
        yield session

@asynccontextmanager
async def get_db_cm() -> AsyncSession:
    """
    Provides an asynchronous context manager for generating database sessions.
    This utility is used to ensure proper cleanup and resource management of
    database connections for asynchronous frameworks.

    :return: An asynchronous database session managed by the context
        manager.
    :rtype: AsyncSession
    """
    async with AsyncSessionLocal() as session:
        yield session
