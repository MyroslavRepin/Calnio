import logging
from backend.app.core.config import settings
from notion_client import Client
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
    page_id_url: str = Form(...),

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
    notion = Client(auth=integration.access_token)

    page_id = page_id_url
    # page = notion.pages.retrieve("26ba555872b480faa752d00bb77d7e3c")
    page = notion.pages.retrieve(page_id=page_id)
    # pyright: ignore[reportArgumentType]
    page_url = page.get("url", f"https://www.notion.so/{page_id}")
    # pyright: ignore[reportArgumentType]
    notion_page = NotionTask.from_notion(page)

    content = {
        "title": notion_page.title,
        "is_done": notion_page.done,
        "description": notion_page.description,
        "url": notion_page.notion_page_url
    }

    await async_create_task(
        db=db,
        user_id=user_id,
        notion_url=notion_page.notion_page_url,
        notion_page_id=page_id,
        title=notion_page.title,
        description=notion_page.description,
        task_date=notion_page.task_date,
        status=notion_page.status,
        select_option=notion_page.select_option,
        done=notion_page.done,
        priority=notion_page.priority
    )

    content = {
        "title": notion_page.title,
        "description": notion_page.description,
        "is_done": notion_page.done,
        "url": notion_page.notion_page_url,
        "id": notion_page.notion_page_id
    }
    # return templates.TemplateResponse(
    #     "tasks.html",
    #     {"request": request, }
    # )
    return JSONResponse(content=content)


@router.get("/dashboard/pages")
async def show_form(request: Request):
    return templates.TemplateResponse("tasks.html", {"request": request})
