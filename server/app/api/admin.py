import os

from server.utils.security.utils import check_if_user_authorized
from server.db.deps import async_get_db
from server.services.crud.users import async_get_by_id

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Request, Depends, status, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.exceptions import HTTPException

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(
    BASE_DIR, "..", "..", "..", "frontend"))

templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates/routes"))


@router.get("/admin", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(async_get_db),
):
    """Admin Dashboard (superusers only)."""
    auth = await check_if_user_authorized(request)
    if not auth.get("authorized"):
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    user_id = auth["user_id"]
    user = await async_get_by_id(db, user_id)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    if not user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    # Render an admin page. Reuse existing users listing template for now.
    # (This keeps the route HTML-based and avoids returning raw ORM objects.)
    return templates.TemplateResponse(
        "users.html",
        {
            "request": request,
            "user": {"id": user.id, "email": user.email, "username": user.username},
            "users": [user],
        },
        status_code=status.HTTP_200_OK,
        headers=response.headers,
    )
