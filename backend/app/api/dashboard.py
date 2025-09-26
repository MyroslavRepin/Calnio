import os

from notion_client import AsyncClient

from backend.app.db.database import AsyncSessionLocal
from backend.app.security.jwt_config import security
from backend.app.security.utils import access_token_required, refresh_access_token, create_hash, \
    check_if_user_authorized
from backend.app.db.deps import async_get_db
from backend.app.crud.users import async_get_by_id, async_update_by_id, async_update_password_by_id
from backend.app.core.config import settings
from backend.app.models import UserNotionTask, User

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from fastapi import APIRouter, Request, Form, Depends, status, Query, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.exceptions import HTTPException

import logging
import colorlog

from backend.app.crud.tasks import add_tasks_to_db, delete_pages_by_ids, get_all_ids, update_pages_by_ids

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(
    BASE_DIR, "..", "..", "..", "frontend"))

templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(async_get_db),
    success: int | None = Query(None),
):
    data = await check_if_user_authorized(request)

    if not data["authorized"]:
        return RedirectResponse("/login", status_code=302)

    user_id = data["user_id"]
    user = await async_get_by_id(db, user_id)

    OAuth_url = settings.notion_oauth_url

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Select users tasks via user_id
    stmt = select(UserNotionTask).where(UserNotionTask.user_id == user_id)

    result = await db.execute(stmt)
    tasks = result.scalars().all()

    # Selecting user
    stmt = select(User).where(User.id == user_id)
    result_user = await db.execute(stmt)
    user_obj = result_user.scalars().first()

    # Making list of data from db

    titles = []
    descriptions = []
    priorities = []
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    integration = user.notion_integration

    if not integration:
        raise HTTPException(
            status_code=404, detail="Notion integration not found")

    for task in tasks:
        titles.append(task.title)
        descriptions.append(task.description)
        priorities.append(task.priority)

    html_content = templates.get_template("dashboard.html").render(
        request=request,
        username=user.username,
        email=user.email,
        success=success,
        OAuth_url=OAuth_url,
        tasks=tasks,
        user_obj=user_obj
    )
    return HTMLResponse(content=html_content, headers=response.headers, status_code=200)


@router.post("/update-profile")
async def update_profile(
    request: Request,
    response: Response,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    sync_interval: int = Form(default=30),
    db: AsyncSession = Depends(async_get_db)
):
    try:
        # All correct code if user authorized

        # Decode payload and check if expired. Returns dict
        payload = await access_token_required(request)
        user_id = int(payload["sub"])
        # print(user_id)
    except HTTPException:
        # Если токен невалиден или отсутствует — редирект или HTML
        try:
            payload = await refresh_access_token(request, response)
            user_id = int(payload["sub"])  # важно: user_id тут тоже нужен

        except HTTPException:
            return RedirectResponse("/login", 401)

    user = await async_get_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate sync_interval (must be between 5 and 1440 minutes - 5 min to 24 hours)
    if sync_interval < 5 or sync_interval > 1440:
        sync_interval = 30  # Default to 30 minutes if invalid

    await async_update_by_id(db=db, user_id=user_id, new_username=username, new_email=email)

    await async_update_password_by_id(db=db, user_id=user_id, new_password=password)
    
    # Update sync_interval
    user.sync_interval = sync_interval
    db.add(user)
    await db.commit()
    
    # Update the scheduler job with new interval
    from backend.app.services.scheduler import sync_scheduler
    if user.notion_integration and user.notion_integration.access_token:
        sync_scheduler.add_user_sync_job(user_id, sync_interval)
    
    return RedirectResponse(url="/dashboard?success=1", status_code=status.HTTP_302_FOUND)
