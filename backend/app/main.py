import os
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR,
          "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse('login.html', context={'request': request})


@app.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
    return templates.TemplateResponse('signup.html', context={'request': request})
