from backend.app.models import users as user_models
from backend.app.db.database import AsyncSession, async_engine
from sqladmin import ModelView
from sqladmin import Admin
import os
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import atexit

from backend.app.api import login, signup, landing, dashboard, users, logout, refresh, error_404
from backend.app.api.oauth import notion_callback
from backend.app.api.integrations.notion import pages
from backend.app import version
from backend.app.middleware.ignore_logging import IgnoreSpecificPathsMiddleware
from backend.app.services.scheduler import sync_scheduler

import logging

# logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
# logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)


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


# Initialize scheduler on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the scheduler and set up existing user sync jobs."""
    sync_scheduler.start()
    
    # Initialize sync jobs for existing users with notion integrations
    from backend.app.db.database import AsyncSessionLocal
    from backend.app.models.users import User
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as db:
        try:
            # Get all active users with notion integrations
            stmt = select(User).where(User.is_active == True)
            result = await db.execute(stmt)
            users = result.scalars().all()
            
            for user in users:
                if user.notion_integration and user.notion_integration.access_token:
                    sync_scheduler.add_user_sync_job(user.id, user.sync_interval)
                    
            logging.info(f"Initialized sync jobs for {len([u for u in users if u.notion_integration and u.notion_integration.access_token])} users")
            
        except Exception as e:
            logging.error(f"Failed to initialize user sync jobs: {e}")
    
    logging.info("Application startup completed with scheduler initialized")


# Cleanup scheduler on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup scheduler on application shutdown."""
    sync_scheduler.shutdown()
    logging.info("Application shutdown completed")


# Also ensure scheduler shuts down on process termination
atexit.register(sync_scheduler.shutdown)
