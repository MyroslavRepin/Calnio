import logging

from server.db.models import users as user_models
from server.db.models import tasks as task_models
from server.db.models.notion_integration import UserNotionIntegration as  notion_integration_models
from server.db.database import async_engine
from sqladmin import ModelView
from sqladmin import Admin
import os
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from server.app.api.auth import router as auth_router
from server.app.api import landing, dashboard, refresh_cookies
from server.app.api.errors import error_404

from server.integrations.oauth.notion import notion_callback
from server.integrations.notion import pages
from server.app import version
from server.app.middleware.ignore_logging import IgnoreSpecificPathsMiddleware
from server.services.scheduler_service import start_scheduler, shutdown_scheduler
from server.app.api.webhooks.notion_webhooks import router as notion_webhook_router
from server.db.redis_client import init_redis, close_redis

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
app.include_router(notion_webhook_router)


class UserAdmin(ModelView, model=user_models.User):
    column_list = [user_models.User.id, user_models.User.email, user_models.User.username, user_models.User.is_superuser]


admin = Admin(app, async_engine)
admin.add_view(UserAdmin)

# APScheduler starting
@app.on_event("startup")
def on_startup():
    # Register jobs here, e.g.
    # start_scheduler()
    pass

@app.on_event("shutdown")
def on_shutdown():
    # shutdown_scheduler()
    pass


@app.on_event("startup")
async def on_startup_async():
    await init_redis()

@app.on_event("shutdown")
async def on_shutdown_async():
    await close_redis()