import asyncio
# from aiocaldav import DAVClient
from caldav import DAVClient
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
    async with async_get_db_cm() as db:
        logger.info(f"Fetching user data for user ID {user_id}")
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
    if not user:
        logger.error(f"User with id {user_id} not found")
        raise ValueError("User not found")

    icloud_username = str(user.icloud_email)
    icloud_password = str(user.app_specific_password)

    # Auth layer
    def _get_caldav_client():
        logger.debug("Initializing CalDav client...")
        try:
            client = DAVClient(
                url="https://caldav.icloud.com/",
                username=icloud_username,
                password=icloud_password
            )
            # Force a simple request to validate credentials
            try:
                client.principal()
            except Exception:
                logger.error(f"CalDav authentication failed for user ID {user_id} email: {icloud_username}, password: {icloud_password}")
                raise ValueError("CalDAV authentication failed")
            logger.debug("CalDav client initialized and authenticated")
            return client
        except Exception as e:
            logger.error("Failed to initialize CalDav client")
            raise e

    # Running as async not blocking the main thread
    return await asyncio.to_thread(_get_caldav_client)
