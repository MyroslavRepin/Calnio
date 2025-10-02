import logging

from backend.db.models import users as user_models
from backend.db.database import async_engine
from sqladmin import ModelView
from sqladmin import Admin
import os
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from backend.app.api.auth import router as auth_router
from backend.app.api import landing, dashboard, refresh_cookies
from backend.app.api.errors import error_404

from backend.integartions.oauth.oauth import notion_callback
from backend.integartions.notion import pages
from backend.app import version
from backend.app.middleware.ignore_logging import IgnoreSpecificPathsMiddleware
from backend.services.scheduler_service import start_scheduler, shutdown_scheduler

# Remove direct logging.basicConfig and use config

logging.basicConfig(
    level=logging.DEBUG,  # or INFO
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

# Creating Main App
app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "frontend"))
templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))

# Setting up handler 500 error


@app.exception_handler(Exception)
async def internal_server_error_handler(request, exc):
    # можно логировать exc для отладки
    logging.error(f"💥 Internal server error: {exc}")
    return templates.TemplateResponse(
        "500.html",
        {"request": request},
        status_code=500
    )

# Setting static / templates files into FastAPI
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR,
          "static")), name="static")
app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR,
          "assets")), name="assets")
app.mount(
    "/fonts", StaticFiles(directory=os.path.join(FRONTEND_DIR, "fonts")), name="fonts")

app.add_middleware(IgnoreSpecificPathsMiddleware)

app.include_router(auth_router)
app.include_router(landing.router)
app.include_router(dashboard.router)
app.include_router(version.router)
app.include_router(refresh_cookies.router)
app.include_router(notion_callback.router)
app.include_router(error_404.router)
app.include_router(pages.router)


class UserAdmin(ModelView, model=user_models.User):
    column_list = [user_models.User.id, user_models.User.email]


admin = Admin(app, async_engine)
admin.add_view(UserAdmin)

# APScheduler starting
@app.on_event("startup")
def on_startup():
    # Register jobs here, e.g. interval job every 30 seconds
    start_scheduler()

@app.on_event("shutdown")
def on_shutdown():
    shutdown_scheduler()
