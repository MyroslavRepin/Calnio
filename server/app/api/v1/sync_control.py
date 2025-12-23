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


@router.post("/v1/settings/sync")
async def sync_control(
    request: Request,
    db: AsyncSession = Depends(async_get_db),
):
    request_example = {
        'user_id': ...,
        'action': 'start',  # or 'stop'
        'function': 'sync_caldav_to_db'
    }


