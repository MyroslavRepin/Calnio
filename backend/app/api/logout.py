import os

from fastapi import APIRouter, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.app.security.jwt_config import config

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(
    BASE_DIR, "..", "..", "..", "frontend"))

templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))


@router.post("/logout")
async def logout(response: Response):
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
