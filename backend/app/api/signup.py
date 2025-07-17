import os
from passlib.context import CryptContext

from fastapi import APIRouter, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from backend.app.db.database import AsyncSessionLocal, async_engine
from backend.app.db.deps import async_get_db
from backend.app.crud.users import async_create_user
from backend.app.schemas.users import UserCreate
from backend.app.security.utils import create_hash

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(
    BASE_DIR, "..", "..", "..", "frontend"))

templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


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
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Passwords does not match!",
            "username": username,
            "email": email
        })
    errors = {}
    try:
        # Trying create error

        # Creating user obj
        user = UserCreate(
            username=username,
            email=email,
            hashed_password=create_hash(password)
        )
        await async_create_user(db=db, user=user)  # Running function

        # Redirecting to login if succes
        return RedirectResponse('/login', status_code=303)

    # If errors
    except ValueError as e:
        print(e)
        return templates.TemplateResponse(
            "signup.html",
            {
                "request": request,
                "error": str(e),
                "username": username,
                "email": email
            },
            status_code=200
        )
