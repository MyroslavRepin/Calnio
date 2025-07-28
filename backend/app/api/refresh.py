import os

from fastapi import APIRouter, Request, Form, Depends, HTTPException, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from backend.app.security.jwt_config import security, config

router = APIRouter()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(
    BASE_DIR, "..", "..", "..", "frontend"))

templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))


@router.post("/refresh")
async def refresh_token(request: Request, response: Response):
    try:
        # Проверяем и извлекаем payload из refresh_token cookie
        refresh_payload = await security.refresh_token_required(request)

        # Создаём новый access токен на основе user_id из payload
        new_access_token = security.create_access_token(refresh_payload.sub)

        # Устанавливаем новый access_token в cookie (перезаписываем старый)
        response.set_cookie(
            key=config.JWT_ACCESS_COOKIE_NAME,
            value=new_access_token,
            httponly=True,
            samesite="lax",
            secure=False,  # в продакшене ставь True при HTTPS
        )

        return {"message": "Access token refreshed"}
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=401, detail="Invalid refresh token or expired")
