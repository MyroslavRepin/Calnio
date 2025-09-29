from notion_client import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
import os
import logging

from fastapi import APIRouter, Request, Depends, HTTPException, Response, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from backend.app.services.crud.users import async_get_by_id
from backend.app.db.deps import async_get_db
from backend.app.security.utils import check_if_user_authorized
from backend.app.services.notion_sync import notion_sync_background
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
        logging.error(f"User {user_id} does not have a Notion integration.")
        raise HTTPException(
            status_code=404, detail="Notion integration not found")

    # Creating a client for user
    notion = AsyncClient(auth=integration.access_token)

    # # Debug logging to ensure notion client is valid
    # if not hasattr(notion, "search"):
    #     logging.error(f"Invalid Notion client created for user {user_id}.")
    #     raise HTTPException(
    #         status_code=500, detail="Failed to create Notion client.")

    # Get tasks from notion db and saving to bd (background task)
    logging.debug(f"notion type={type(notion)}, user_id={user_id}")
    background_tasks.add_task(notion_sync_background, db=db, notion=notion, user_id=user_id)
    return RedirectResponse("/dashboard", 302)
