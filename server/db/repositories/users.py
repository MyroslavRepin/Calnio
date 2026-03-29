from sqlalchemy.ext.asyncio.session import AsyncSession

from server.db.models.users import User
from server.core.logging_config import logger
from sqlalchemy import select

class UserRepository:
    def __init__(self):
        self.model = User

    async def create(self, db: AsyncSession, **kwargs):
        user = self.model(**kwargs)
        db.add(user)
        try:
            await db.commit()
            await db.refresh(user)
            logger.debug(f"User {user.username} created")
            return user
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            await db.rollback()
            raise

    async def update(self, db: AsyncSession, user_id: int, **kwargs):
        stmt = select(self.model).where(self.model.id == user_id)
        try:
            result = await db.execute(stmt)
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            raise
        user = result.scalars().first()
        if not user:
            return None
        
        for key, value in kwargs.items():
            if value is not None:
                setattr(user, key, value)
        try:
            await db.commit()
            await db.refresh(user)
            logger.debug(f"User {user_id} updated")
            return user
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            await db.rollback()
            raise

    async def get_user_by_id(self, db: AsyncSession, user_id: int):
        """
        Returns user if found by ID, otherwise None.
        :param db:
        :param user_id:
        :return:
        """
        stmt = select(self.model).where(self.model.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        if not user:
            return None

        return user
