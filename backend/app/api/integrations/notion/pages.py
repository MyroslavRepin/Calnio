import logging
from backend.app.core.config import settings
from notion_client import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import os

from fastapi import APIRouter, Request, Form, Depends, HTTPException, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from backend.app.schemas.notion_pages import NotionTask
from backend.app.crud.users import async_get_by_id
from backend.app.db.deps import async_get_db
from backend.app.security.utils import access_token_required, refresh_access_token
from backend.app.crud.tasks import async_create_task
from backend.app.tools.notion.utils import get_all_ids, add_tasks_to_bd
router = APIRouter()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(
    BASE_DIR, "..", "..", "..", "..", "..", "frontend"))

templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))


# Optimize: Take page_id from form and using it dave to bd, and input success message
@router.post("/dashboard/pages")
async def pages(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(async_get_db),
    page_id: str = Form(...),

):
    try:
        # Decode payload and check if expired. Returns dict
        print("Cookies received")

        payload = await access_token_required(request)
        user_id = int(payload["sub"])

    except HTTPException:
        # Если токен невалиден или отсутствует — редирект или HTML
        try:
            logging.info("Trying update access token")
            payload = await refresh_access_token(request, response)
            user_id = int(payload["sub"])  # важно: user_id тут тоже нужен

        except HTTPException:
            return RedirectResponse("/login", 401)

    user = await async_get_by_id(db, user_id)

    # Checking if user is not None
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    integration = user.notion_integration

    if not integration:
        raise HTTPException(
            status_code=404, detail="Notion integration not found")

    # Creating client for user
    notion = AsyncClient(auth=integration.access_token)

    result = await add_tasks_to_bd(db=db, notion=notion, user_id=user_id)

    return result


@router.get("/dashboard/pages")
async def show_form(request: Request):
    return templates.TemplateResponse("tasks.html", {"request": request})
