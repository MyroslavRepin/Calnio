import asyncio
import datetime
from typing import Optional
from sqlalchemy import select
from tabulate import tabulate
from hashlib import sha256

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.tasks import UserNotionTask
from backend.app.models.users import User
from backend.app.schemas.users import UserCreate
from backend.app.db.database import async_engine
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


async def async_update_by_id(db: AsyncSession, user_id, new_username, new_email: str | None):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if not new_email:
        if user:
            user.username = new_username

            await db.commit()
            await db.refresh(user)
    if new_email:
        if user:
            user.username = new_username
            user.email = new_email
            await db.commit()
            await db.refresh(user)


async def async_update_password_by_id(db: AsyncSession, user_id, new_password):
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    if user:
        user.hashed_password = create_hash(new_password)
        await db.commit()
        await db.refresh(user)


async def async_get_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    return user


async def async_create_task(
    db: AsyncSession,
    user_id: int,
    title: str,
    notion_url: str,
    notion_page_id: str,
    description: Optional[str] = None,
    task_date: Optional[str] = None,
    status: Optional[str] = None,
    done: bool = False,
    priority: Optional[str] = None,
    select_option: Optional[str] = None,
) -> UserNotionTask:
    """
    Создаёт задачу в таблице notion_tasks для указанного пользователя.
    """

    new_task = UserNotionTask(
        user_id=user_id,
        title=title,
        notion_url=notion_url,
        notion_page_id=notion_page_id,
        description=description,
        task_date=task_date,
        status=status,
        done=done,
        priority=priority,
        select_option=select_option,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(new_task)
    await db.commit()
    # чтобы вернуть объект с id и заполненными полями
    await db.refresh(new_task)
    return new_task
