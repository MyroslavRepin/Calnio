import os

from backend.app.db.database import AsyncSessionLocal
from backend.app.security.jwt_config import security
from backend.app.security.utils import access_token_required

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.exceptions import HTTPException

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(
    BASE_DIR, "..", "..", "..", "frontend"))

templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        payload = await access_token_required(request)
    except HTTPException:
        # ❌ Если токен невалиден или отсутствует — редирект или HTML
        return templates.TemplateResponse("unauthorized.html", {"request": request}, status_code=401)
    return templates.TemplateResponse("dashboard.html", {"request": request})
