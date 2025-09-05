from backend.app.models import users as user_models
from backend.app.db.database import AsyncSession, async_engine
from sqladmin import ModelView
from sqladmin import Admin
import os
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from backend.app.api import login, signup, landing, dashboard, users, logout, refresh, error_404
from backend.app.api.oauth import notion_callback
from backend.app import version
from backend.app.middleware.ignore_logging import IgnoreSpecificPathsMiddleware


app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "frontend"))

templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR,
          "static")), name="static")

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


class UserAdmin(ModelView, model=user_models.User):
    column_list = [user_models.User.id, user_models.User.email]


admin = Admin(app, async_engine)
admin.add_view(UserAdmin)

# app.add_middleware(IgnoreSpecificPathsMiddleware)
