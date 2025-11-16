import asyncio
import os
import sys
import logging
from loguru import logger

from server.services.scheduler.scheduler_service import shutdown_scheduler, start_scheduler

from litestar import Litestar, get
from litestar.plugins.prometheus import PrometheusConfig, PrometheusController
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.exceptions import HTTPException



# === Intercept standard logging and redirect to Loguru ===
class InterceptHandler(logging.Handler):
    """Intercept standard logging messages and redirect them to Loguru."""
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where the logged message originated
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

# Remove default Loguru handler and add custom one
logger.remove()
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
           "<level>{message}</level>",
    level="DEBUG",
)

os.makedirs("logs", exist_ok=True)
logger.add("logs/app_{time:YYYY-MM-DD}.log",
           rotation="1 day",
           retention="14 days",
           compression="zip",
           format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
           level="DEBUG",
           backtrace=True,
           diagnose=True)

# Intercept all standard logging and redirect to Loguru
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

# Redirect uvicorn loggers to Loguru
for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
    logging_logger = logging.getLogger(logger_name)
    logging_logger.handlers = [InterceptHandler()]
    logging_logger.propagate = False

def handle_exception(exc_type, exc_value, exc_traceback):
    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

logger.info("Loguru initialized")

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqladmin import Admin
from sqladmin import ModelView

from server.app.api import dashboard, landing, refresh_cookies
from server.app.api.auth import router as auth_router
from server.app.api.errors import error_404
from server.app.api.webhooks.notion_webhooks import router as notion_webhook_router
from server.app import version
from server.db.database import async_engine
from server.db.models import users as user_models
from server.db.redis_client import close_redis, init_redis
from server.integrations.notion import pages
from server.integrations.oauth.notion import notion_callback
from server.middleware.ignore_logging import IgnoreSpecificPathsMiddleware
from server.services.postgres_trigger import listen_to_postgres
from server.services.caldav.user_calendars import sync_user_calendars

# Creating Main App
app = FastAPI()

from prometheus_fastapi_instrumentator import Instrumentator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "frontend"))
templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))

# Setting up handler 500 error
@app.exception_handler(Exception)
async def internal_server_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
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
    asyncio.create_task(listen_to_postgres("notion_tasks_channel"))
    start_scheduler()

@app.on_event("shutdown")
def on_shutdown():
    shutdown_scheduler()


@app.on_event("startup")
async def on_startup_async():
    await init_redis()

@app.on_event("shutdown")
async def on_shutdown_async():
    await close_redis()
