import os
from authx import AuthX, AuthXConfig

from fastapi import APIRouter, Request, Form, Depends, HTTPException, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from backend.app.schemas.users import UserLogin

router = APIRouter()


#! JWT Token CONFIG
config = AuthXConfig()
config.JWT_SECRET_KEY = "secret_key"
config.JWT_ACCESS_COOKIE_NAME = "acces_token"
config.JWT_TOKEN_LOCATION = ["cookies"]

security = AuthX(config=config)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(
    BASE_DIR, "..", "..", "..", "frontend"))

templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post('/login')
async def login_post(response: Response, creds: UserLogin = Depends(UserLogin.as_form)):
    if creds.email == "myroslavrepin@gmail.com" and creds.password == "myroslav0818":
        token = security.create_access_token(uid="12456")
        response.set_cookie(config.JWT_ACCESS_COOKIE_NAME, token)
        print(token)
        return {"acces_token": token}
    raise HTTPException(401, detail='Incorrect data')
