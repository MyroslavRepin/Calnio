from fastapi import Depends, Response, APIRouter

from server.app.api.v1.auth import jwt_service
from server.core.config import settings
from server.core.jwt_config import auth

router = APIRouter()

@router.post("/auth/refresh")
async def refresh_tokens(
    response: Response,
    payload: dict = Depends(auth.refresh_token_required),
):
    user_id = payload["sub"]

    new_access = jwt_service.create_access_token(user_id)
    response.set_cookie(
        key=settings.jwt_access_cookie_name,
        value=new_access,
        httponly=True,
        samesite="lax",
    )

    return {"message": "Token refreshed", "user_id": user_id}