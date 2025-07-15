import asyncio
from sqlalchemy import select
from tabulate import tabulate
from hashlib import sha256

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.users import User
from backend.app.schemas.users import UserCreate
from backend.app.db.database import async_engine


async def get_users(db: AsyncSession):
    stmt = select(User)
    result = await db.execute(stmt)
    users = result.scalars().all()
    return users


def async_print_users_table(users):

    rows = []
    for u in users:
        rows.append([u.id, u.username, u.email, u.is_superuser])
    print(tabulate(rows, headers=["ID", "Username",
          "Email", "Is Admin"], tablefmt="psql"))


async def async_create_user(db: AsyncSession, users: list[UserCreate]):
    for user in users:
        try:
            async_engine.echo = False
            hashed_password = sha256(user.password.encode()).hexdigest()
            db_user = User(
                email=user.email,
                username=user.username,
                hashed_password=hashed_password,
                is_superuser=user.is_superuser
            )
            db.add(db_user)
            await db.commit()
            await db.refresh(db_user)
            return db_user
        except IntegrityError:
            await db.rollback()
            print(f"⚠️ Skipped (duplicate): {user.email}")


async def async_delete_by_id(db: AsyncSession, user_id):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if user:
        await db.delete(user)
        await db.commit()
        print(f"User: {user.email} deleted")
        await db.close()
        return user.email
    await db.close()
    return False


async def async_update_by_id(db: AsyncSession, user_id, new_username):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if user:
        user.username = new_username

        await db.commit()
        await db.refresh(user)
