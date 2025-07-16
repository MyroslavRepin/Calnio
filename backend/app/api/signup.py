import os
from passlib.context import CryptContext

from fastapi import APIRouter, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from backend.app.db.database import AsyncSessionLocal, async_engine
from backend.app.db.deps import async_get_db
from backend.app.crud.users import async_create_user
from backend.app.schemas.users import UserCreate

from sqlalchemy.ext.asyncio import AsyncSession

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
    try:
        hashed_password = pwd_context.hash(password)
        user = UserCreate(
            username=username,
            email=email,
            hashed_password=password
        )
        created_user = await async_create_user(db=db, user=user)

        if not created_user:
            return templates.TemplateResponse("signup.html", {
                "request": request,
                "error": "User with this email already exist",
                "username": username,
                "email": email
            })
    except Exception as e:
        print(f"Error occured: {e}")
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Error while creating user",
            "username": username,
            "email": email
        })

    return RedirectResponse('/login', status_code=303)
