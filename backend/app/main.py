import logging

from backend.app.models import users as user_models
from backend.app.db.database import AsyncSession, async_engine
from sqladmin import ModelView
from sqladmin import Admin
import os
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from backend.app.api import login, signup, landing, dashboard, users, logout, refresh, error_404
from backend.app.api.oauth import notion_callback
from backend.app.api.integrations.notion import pages
from backend.app import version
from backend.app.middleware.ignore_logging import IgnoreSpecificPathsMiddleware
from backend.app.core.config import configure_logging
from backend.app.services.schedulor import sync_service, start_scheduler, shutdown_scheduler
from backend.app.db.deps import async_get_db
import asyncio

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

app.include_router(login.router)
app.include_router(signup.router)
app.include_router(landing.router)
app.include_router(dashboard.router)
app.include_router(version.router)
app.include_router(users.router)
app.include_router(logout.router)
app.include_router(refresh.router)
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
