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
# если у тебя pwd_context там
from backend.app.security.utils import pwd_context, create_hash


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


async def async_create_user(db: AsyncSession, user: UserCreate):
    query = select(User).filter(
        (User.email == user.email) | (User.username == user.username)
    )
    result = await db.execute(query)
    existing_user = result.scalars().first()

    if existing_user:
        raise ValueError(
            f"⚠️ Пользователь с email '{user.email}' или username '{user.username}' уже существует."
        )

    try:
        # hashed_password = pwd_context.hash(user.hashed_password)
        db_user = User(
            email=user.email,
            username=user.username,
            # For real its firts layer of hash. user.hashed_password did not hashed before this step
            hashed_password=user.hashed_password,
            is_superuser=user.is_superuser
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user  # возвращаем созданного пользователя
    except IntegrityError:
        await db.rollback()
        raise ValueError(f"⚠️ База данных: email или username уже существует.")
    except Exception as e:
        await db.rollback()
        raise ValueError(f"❌ Ошибка при создании пользователя: {e}")


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
