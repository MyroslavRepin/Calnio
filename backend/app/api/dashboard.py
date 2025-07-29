import os

from backend.app.db.database import AsyncSessionLocal
from backend.app.security.jwt_config import security
from backend.app.security.utils import access_token_required, refresh_access_token
from backend.app.db.deps import async_get_db
from backend.app.crud.users import async_get_by_id, async_update_by_id

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Request, Form, Depends, status, Query
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
    db: AsyncSession = Depends(async_get_db),
    success: int | None = Query(None),
):
    try:
        # Decode payload and check if expired. Returns dict
        payload = await access_token_required(request)
        user_id = int(payload["sub"])
        print(user_id)

    except HTTPException:
        # Если токен невалиден или отсутствует — редирект или HTML
        return templates.TemplateResponse("unauthorized.html", {"request": request}, status_code=401)

    user = await async_get_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Передаём имя пользователя в шаблон
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": user.username,
        "email": user.email,
        "success": success,
    })


@router.post("/update-profile")
async def update_profile(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    db: AsyncSession = Depends(async_get_db)
):
    try:
        #! All correct code if user authorized

        # Decode payload and check if expired. Returns dict
        payload = await access_token_required(request)
        user_id = int(payload["sub"])
        # print(user_id)
    except HTTPException:
        # ❌ Если токен невалиден или отсутствует — редирект или HTML
        return templates.TemplateResponse("unauthorized.html", {"request": request}, status_code=401)

    user = await async_get_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await async_update_by_id(db=db, user_id=user_id, new_username=username, new_email=email)
    return RedirectResponse(url="/dashboard?success=1", status_code=status.HTTP_302_FOUND)
