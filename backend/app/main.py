import os
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from backend.app.api import login, signup, landing, dashboard, users
from backend.app import version

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
