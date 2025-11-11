import os

from server.utils.security.utils import access_token_required, refresh_access_token, check_if_user_authorized
from server.db.deps import async_get_db
from server.services.crud.users import async_get_by_id, async_update_by_id, async_update_password_by_id
from server.app.core.config import settings
from server.db.models import UserNotionTask, User

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from fastapi import APIRouter, Request, Form, Depends, status, Query, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.exceptions import HTTPException

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
    stmt = select(UserNotionTask).where(
        UserNotionTask.user_id == user_id,
        or_(UserNotionTask.deleted.is_(False), UserNotionTask.deleted.is_(None))
    )

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
            status_code=404, detail="Notion integrations not found")

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

    await async_update_by_id(db=db, user_id=user_id, new_username=username, new_email=email)

    await async_update_password_by_id(db=db, user_id=user_id, new_password=password)
    return RedirectResponse(url="/dashboard?success=1", status_code=status.HTTP_302_FOUND)
