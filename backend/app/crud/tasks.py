import asyncio
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from tabulate import tabulate
from hashlib import sha256
import uuid

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.tasks import UserNotionTask
from backend.app.models.users import User
from backend.app.schemas.users import UserCreate
from backend.app.schemas.notion_pages import NotionTask
from backend.app.db.database import async_engine
from backend.app.security.utils import pwd_context, create_hash


async def async_create_task(
    db: AsyncSession,
    user_id: int,
    title: str,
    notion_page_id: str,
    notion_url: str,
    description: str | None = None,
    task_date: str | None = None,  # приходит строкой из формы или NotionTask
    status: str | None = None,
    done: bool = False,
    priority: str | None = None,
    select_option: str | None = None,
) -> UserNotionTask:

    # Проверяем, есть ли уже задача с таким page_id
    stmt = select(UserNotionTask).where(
        UserNotionTask.user_id == user_id,
        UserNotionTask.notion_page_id == notion_page_id
    )
    result = await db.execute(stmt)
    existing_task = result.scalar_one_or_none()

    # Конвертируем task_date в datetime, если есть
    task_date_dt = None
    if task_date:
        task_date_dt = datetime.fromisoformat(task_date)

    if existing_task:
        # обновляем существующую запись
        existing_task.title = title
        existing_task.notion_url = notion_url
        existing_task.description = description
        existing_task.task_date = task_date_dt
        existing_task.status = status
        existing_task.done = done
        existing_task.priority = priority
        existing_task.select_option = select_option
        await db.commit()
        await db.refresh(existing_task)
        return existing_task

    # создаём новую задачу
    new_task = UserNotionTask(
        id=str(uuid.uuid4()),
        user_id=user_id,
        notion_page_id=notion_page_id,
        notion_url=notion_url,
        title=title,
        description=description,
        task_date=task_date_dt,
        status=status,
        done=done,
        priority=priority,
        select_option=select_option
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task
