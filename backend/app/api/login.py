import os

from fastapi import APIRouter, Request, Form, Depends, HTTPException, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from backend.app.schemas.users import UserLogin
from backend.app.security.jwt_config import config, security
from backend.app.models.users import User
from backend.app.db.deps import async_get_db
from backend.app.security.utils import verify_password, check_if_user_authorized

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(
    BASE_DIR, "..", "..", "..", "frontend"))

templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    data = await check_if_user_authorized(request)
    if data["authorized"]:
        return RedirectResponse("/dashboard", status_code=302)
    # Check for error in query params (for GET requests after redirect)
    error = request.query_params.get("error")
    return templates.TemplateResponse("login.html", {"request": request, "error": error})


@router.post('/login')
async def login_post(
    request: Request,
    creds: UserLogin = Depends(UserLogin.as_form),
    db: AsyncSession = Depends(async_get_db)
):
    # Check password length before attempting to hash (bcrypt has 72-byte limit)
    if len(creds.password.encode('utf-8')) > 72:
        return RedirectResponse("/login?error=Password+is+too+long+(max+72+bytes)", status_code=303)
    
    query = select(User).where(
        (User.email == creds.login) | (User.username == creds.login))
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    data = await check_if_user_authorized(request)
    if data["authorized"]:
        return RedirectResponse("/dashboard", status_code=302)

    if not user or user.hashed_password is None or not verify_password(
        plain_password=creds.password,
        hashed_password=user.hashed_password
    ):
        # Pass error as query param for GET (so refresh doesn't resubmit form)
        return RedirectResponse("/login?error=Incorrect+email+or+password!", status_code=303)

    # Создаём токены
    access_token = security.create_access_token(uid=str(user.id))
    refresh_token = security.create_refresh_token(uid=str(user.id))
    redirect_response = RedirectResponse("/dashboard", status_code=303)

    # Ставим куки
    redirect_response.set_cookie(
        config.JWT_ACCESS_COOKIE_NAME,
        access_token,
        httponly=True,
        samesite="none",
        secure=True,
        path="/",
    )
    redirect_response.set_cookie(
        config.JWT_REFRESH_COOKIE_NAME,
        refresh_token,
        httponly=True,
        samesite="none",
        secure=True,
        path="/",
    )
    return redirect_response
