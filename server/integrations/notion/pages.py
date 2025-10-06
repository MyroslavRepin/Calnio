from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
from server.app.core.logging_config import logger

from fastapi import APIRouter, Request, Depends, HTTPException, Response, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from server.db.models import UserNotionTask, User
from server.services.crud.users import async_get_by_id
from server.db.deps import async_get_db
from server.utils.security.utils import check_if_user_authorized
from server.services.notion_sync import notion_sync_background
from server.integrations.notion.notion_client import get_notion_client
router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(
    BASE_DIR, "..", "..", "..", "..", "..", "frontend"))

templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))


@router.get("/dashboard/pages")
async def pages(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(async_get_db),
    background_tasks: BackgroundTasks = BackgroundTasks,
):
    data = await check_if_user_authorized(request)
    user_id = data["user_id"]
    if not data["authorized"]:
        return RedirectResponse("/login", status_code=302)
    user = await async_get_by_id(db, user_id)

    # Checking if user is not None
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    integration = user.notion_integration

    if not integration:
        logger.error(f"❌ User {user_id} does not have a Notion integration")
        raise HTTPException(
            status_code=404, detail="Notion integrations not found")

    # Creating a client for user
    notion = get_notion_client(integration.access_token)

    # Get tasks from notion db and saving to bd (background task)

    # Setting active_sync to True to start syncing for this user
    user.active_sync = True
    await db.commit()

    logger.debug(f"🔄 Starting background sync for user_id={user_id}")
    background_tasks.add_task(notion_sync_background, db=db, notion=notion, user_id=user_id)
    return RedirectResponse("/dashboard", 302)
