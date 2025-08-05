import os

from backend.app.db.database import AsyncSessionLocal
from backend.app.security.jwt_config import security
from backend.app.security.utils import access_token_required, refresh_access_token
from backend.app.db.deps import async_get_db
from backend.app.crud.users import async_get_by_id, async_update_by_id

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Request, Form, Depends, status, Query, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.exceptions import HTTPException

import logging
import colorlog

router = APIRouter()

#! LOQ SETUP
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    "%(log_color)s%(bold)s%(asctime)s %(levelname)-8s %(reset)s%(white)s%(message)s",
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red,bold',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={},
    style='%'
))

logger = colorlog.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

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
    try:
        # Decode payload and check if expired. Returns dict
        payload = await access_token_required(request)
        user_id = int(payload["sub"])
        print(user_id)

    except HTTPException:
        # Если токен невалиден или отсутствует — редирект или HTML
        try:
            logging.info("Trying update access token")
            payload = await refresh_access_token(request, response)
            user_id = int(payload["sub"])  # важно: user_id тут тоже нужен

        except HTTPException:
            return RedirectResponse("/login", 401)

    user = await async_get_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    html_content = templates.get_template("dashboard.html").render(
        request=request,
        username=user.username,
        email=user.email,
        success=success,
    )

    return HTMLResponse(content=html_content, headers=response.headers, status_code=200)


@router.post("/update-profile")
async def update_profile(
    request: Request,
    response: Response,
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
        # Если токен невалиден или отсутствует — редирект или HTML
        try:
            logging.info("Trying update access token")
            # тут ты, возможно, вернёшь Response с новой кукой
            payload = await refresh_access_token(request, response)
            user_id = int(payload["sub"])  # важно: user_id тут тоже нужен

        except HTTPException:
            return RedirectResponse("/login", 401)

    user = await async_get_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await async_update_by_id(db=db, user_id=user_id, new_username=username, new_email=email)
    return RedirectResponse(url="/dashboard?success=1", status_code=status.HTTP_302_FOUND)
