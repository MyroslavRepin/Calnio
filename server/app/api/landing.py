import os
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from server.utils.security.utils import access_token_required, refresh_access_token
from server.app.version import __version__

router = APIRouter()
# Adding externaly templates, static dir
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(
    BASE_DIR, "..", "..", "..", "frontend"))
router.mount(
    "/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")
router.mount(
    "/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))


@router.get("/", response_class=HTMLResponse)
async def landing(request: Request, response: Response):

    try:
        #! All correct code if user authorized

        # Decode payload and check if expired. Returns dict
        payload = await access_token_required(request)
        user_id = int(payload["sub"])
        return RedirectResponse("/dashboard", 302)
        # print(user_id)
    except HTTPException:
        # Если токен невалиден или отсутствует — редирект или HTML
        try:
            payload = await refresh_access_token(request, response)
            user_id = int(payload["sub"])  # важно: user_id тут тоже нужен

        except HTTPException:
            return templates.TemplateResponse(
                "landing.html",
                {
                    "request": request,
                    "version": __version__,  # вот так правильно
                }
            )
