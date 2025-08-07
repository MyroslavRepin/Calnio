# backend/app/api/login.py

import os

from fastapi import APIRouter, Request, Form, Depends, HTTPException, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from backend.app.schemas.users import UserLogin
from backend.app.security.jwt_config import config, security
from backend.app.models.users import User
from backend.app.db.deps import async_get_db
from backend.app.security.utils import verify_password

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


router = APIRouter()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(
    BASE_DIR, "..", "..", "..", "frontend"))

templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post('/login')
async def login_post(
    request: Request,
    creds: UserLogin = Depends(UserLogin.as_form),
    db: AsyncSession = Depends(async_get_db)
):
    query = select(User).where(
        (User.email == creds.login) | (User.username == creds.login))

    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or user.hashed_password is None or not verify_password(
        plain_password=creds.password,
        hashed_password=user.hashed_password
    ):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Incorrect email or password!"
        })

    access_token = security.create_access_token(uid=str(user.id))
    refresh_token = security.create_refresh_token(uid=str(user.id))
    redirect_response = RedirectResponse("/dashboard", status_code=303)

    return JSONResponse({"access_token": access_token,
                        "refresh_token": refresh_token,
                         "token_type": "bearer", })
