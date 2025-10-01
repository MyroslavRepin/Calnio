import os
from passlib.context import CryptContext

from fastapi import APIRouter, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from backend.app.db.deps import async_get_db
from backend.app.services.crud.users import async_create_user
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
    error = request.query_params.get("error")
    return templates.TemplateResponse("signup.html", {"request": request, "error": error})


@router.post('/signup')
async def signup_post(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: AsyncSession = Depends(async_get_db)
):
    # Check password length before attempting to hash (bcrypt has 72-byte limit)
    if len(password.encode('utf-8')) > 72:
        return RedirectResponse("/signup?error=Password+is+too+long+(max+72+bytes)&username=" + username + "&email=" + email, status_code=303)
    
    if password != confirm_password:
        return RedirectResponse("/signup?error=Passwords+do+not+match!&username=" + username + "&email=" + email, status_code=303)
    try:
        user = UserCreate(
            username=username,
            email=email,
            hashed_password=create_hash(password)
        )
        await async_create_user(db=db, user=user)
        return RedirectResponse('/login', status_code=303)
    except IntegrityError:
        return RedirectResponse("/signup?error=Email+or+username+already+exists!&username=" + username + "&email=" + email, status_code=303)
    except ValueError as e:
        return RedirectResponse(f"/signup?error={str(e)}&username={username}&email={email}", status_code=303)
