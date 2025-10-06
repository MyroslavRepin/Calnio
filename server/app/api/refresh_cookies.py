import os

from fastapi import APIRouter, Request, Response
from fastapi.templating import Jinja2Templates

from server.utils.security.utils import refresh_access_token

router = APIRouter()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(
    BASE_DIR, "..", "..", "..", "frontend"))

templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))


@router.post("/refresh")
async def refresh_token(request: Request, response: Response):
    print("Refresh endpoint called")
    result = await refresh_access_token(request, response)
    return result
