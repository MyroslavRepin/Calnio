import os

from fastapi import APIRouter, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from backend.app.security.jwt_config import config

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(
    BASE_DIR, "..", "..", "..", "frontend"))

templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))


@router.post("/logout")
async def logout(response: Response):
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(
        key=config.JWT_ACCESS_COOKIE_NAME,
        path="/",
        samesite="lax",
        secure=False,
    )
    return response
# @router.get("/signup", response_class=HTMLResponse)
# async def signup(request: Request):
#     return templates.TemplateResponse("signup.html", {"request": request})
# @router.post('/signup')
# async def signup_post(
#     request: Request,
#     username: str = Form(...),
#     email: str = Form(...),
#     password: str = Form(...),
#     confirm_password: str = Form(...),
#     db: AsyncSession = Depends(async_get_db)
# ):
#     if password != confirm_password:
#         return templates.TemplateResponse("signup.html", {
#             "request": request,
#             "error": "Passwords does not match!",
#             "username": username,
#             "email": email
#         })
#     try:
#         hashed_password = pwd_context.hash(password)
#         user = UserCreate(
#             username=username,
#             email=email,
#             hashed_password=password
#         )
#         created_user = await async_create_user(db=db, user=user)
#         if not created_user:
#             return templates.TemplateResponse("signup.html", {
#                 "request": request,
#                 "error": "User with this email already exist",
#                 "username": username,
#                 "email": email
#             })
#     except Exception as e:
#         print(f"Error occured: {e}")
#         return templates.TemplateResponse("signup.html", {
#             "request": request,
#             "error": "Error while creating user",
#             "username": username,
#             "email": email
#         })
#     return RedirectResponse('/login', status_code=303)
