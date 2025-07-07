import os
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from backend.app.db.deps import get_db
from backend.app.crud.users import get_users

router = APIRouter()
# Adding externaly templates, static dir
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(
    BASE_DIR, "..", "..", "..", "frontend"))

templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))


@router.get('/users', response_class=HTMLResponse)
def users(request: Request, db: Session = Depends(get_db)):
    users = get_users(db)
    return templates.TemplateResponse("users.html", {"request": request, "users": users})
