"""
Brutalist Design System Routes
Routes for the new Brutalist Minimalism design system pages
"""

import os
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from server.utils.security.utils import access_token_required, refresh_access_token
from server.app.version import __version__
from datetime import datetime

router = APIRouter()

# Setup templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "..", "frontend"))
templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))


@router.get("/brutalist", response_class=HTMLResponse)
async def brutalist_landing(request: Request):
    """Brutalist design landing page"""
    return templates.TemplateResponse(
        "brutalist-landing.html",
        {
            "request": request,
            "version": __version__,
            "current_year": datetime.now().year,
            "user": None
        }
    )


@router.get("/brutalist/login", response_class=HTMLResponse)
async def brutalist_login(request: Request):
    """Brutalist design login page"""
    return templates.TemplateResponse(
        "brutalist-login.html",
        {
            "request": request,
            "version": __version__,
            "current_year": datetime.now().year,
            "user": None
        }
    )


@router.get("/brutalist/signup", response_class=HTMLResponse)
async def brutalist_signup(request: Request):
    """Brutalist design signup page"""
    return templates.TemplateResponse(
        "brutalist-signup.html",
        {
            "request": request,
            "version": __version__,
            "current_year": datetime.now().year,
            "user": None
        }
    )


@router.get("/brutalist/dashboard", response_class=HTMLResponse)
async def brutalist_dashboard(request: Request, response: Response):
    """Brutalist design dashboard page"""
    try:
        # Try to get user from access token
        payload = await access_token_required(request)
        user_id = int(payload["sub"])
        
        return templates.TemplateResponse(
            "brutalist-dashboard.html",
            {
                "request": request,
                "version": __version__,
                "current_year": datetime.now().year,
                "user": {"id": user_id}
            }
        )
    except HTTPException:
        # Try refresh token
        try:
            payload = await refresh_access_token(request, response)
            user_id = int(payload["sub"])
            
            return templates.TemplateResponse(
                "brutalist-dashboard.html",
                {
                    "request": request,
                    "version": __version__,
                    "current_year": datetime.now().year,
                    "user": {"id": user_id}
                }
            )
        except HTTPException:
            # Redirect to login if not authenticated
            return RedirectResponse("/brutalist/login", status_code=302)
