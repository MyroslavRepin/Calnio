import os

from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from server.app.schemas.users import UserLogin
from server.app.core.config import config, security
from server.db.models import User
from server.db.deps import async_get_db
from server.utils.security.utils import verify_password, check_if_user_authorized
from server.app.core.logging_config import logger

from server.services.crud.users import async_create_user
from server.app.schemas.users import UserCreate
from server.utils.security.utils import create_hash

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from services.email.worker.auth import send_welcome_email

router = APIRouter()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(
    BASE_DIR, "..", "..", "..", "frontend"))

templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates/routes"))

# Login API
@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    data = await check_if_user_authorized(request)
    if data["authorized"]:
        return RedirectResponse("/dashboard", status_code=302)
    # Check for error in query params (for GET requests after redirect)
    error = request.query_params.get("error")
    return templates.TemplateResponse("brutalist-login.html", {"request": request, "error": error})


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


# Signup API
@router.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
    error = request.query_params.get("error")
    return templates.TemplateResponse("brutalist-signup.html", {"request": request, "error": error})


@router.post('/signup')
async def signup_post(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: AsyncSession = Depends(async_get_db)
):
    if password != confirm_password:
        return RedirectResponse("/signup?error=Passwords+do+not+match!&username=" + username + "&email=" + email, status_code=303)
    try:
        user = UserCreate(
            username=username,
            email=email,
            hashed_password=create_hash(password)
        )
        await async_create_user(db=db, user=user)
        # Send welcome email
        try:
            send_welcome_email.delay(to_email=email, username=username)
            logger.debug(f"Welcome email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")

        return RedirectResponse('/login', status_code=303)
    except IntegrityError:
        return RedirectResponse("/signup?error=Email+or+username+already+exists!&username=" + username + "&email=" + email, status_code=303)
    except ValueError as e:
        return RedirectResponse(f"/signup?error={str(e)}&username={username}&email={email}", status_code=303)


# Logout API
@router.post("/logout")
async def logout(response: Response):
    logger.debug("logout POST triggered")
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(
        key=config.JWT_ACCESS_COOKIE_NAME,
        path="/",
        samesite="lax",
        secure=False,
    )
    response.delete_cookie(
        key=config.JWT_REFRESH_COOKIE_NAME,
        path="/",
        samesite="lax",
        secure=False,
    )
    return response
