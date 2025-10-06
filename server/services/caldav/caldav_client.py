import asyncio
from aiocaldav import DAVClient  # правильно: DAVClient
from sqlalchemy import select

from server.db.deps import async_get_db_cm
from server.db.models import User
from server.app.core.logging_config import logger


async def get_caldav_client(user_id):
    """
    Fetches user authentication data from the database, initializes
    a DAVClient instance using the user's iCloud credentials, and
    returns the configured client.

    This asynchronous function is used to retrieve the relevant
    user information from the database and establish a connection
    to the iCloud CalDAV server. The DAVClient will authenticate
    using the provided credentials.

    Parameters:
    user_id : int
        The unique identifier of the user whose authentication
        details need to be retrieved.

    Returns:
    DAVClient
        A configured DAVClient instance authenticated for the
        specified user's iCloud account.
    """
    # todo: realize db search and get data for auth
    async with async_get_db_cm() as db:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()

    icloud_username = str(user.icloud_email)
    icloud_password = str(user.app_specific_password)
    logger.debug(icloud_username)
    logger.debug(icloud_password)

    client = DAVClient(
        url="https://caldav.icloud.com/",
        username=icloud_username,
        password=icloud_password
    )
    logger.debug("CalDav client initialized")
    return client
