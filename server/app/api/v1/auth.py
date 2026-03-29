from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from server.core.config import settings
from server.core.jwt_config import get_authx
from server.core.jwt_service import JWTService
from server.db.models.users import User
from server.db.sessions import get_db
from server.deps.auth_deps import get_current_user
from server.deps.schemas.users_schemes import UserCreate, UserLogin, SignupRequest
from server.utils.security.auth import hash_password
from server.db.repositories.users import UserRepository
from server.core.logging_config import logger
from passlib.hash import argon2


router = APIRouter()

jwt_service = JWTService()

@router.post('/api/v1/auth/signup')
async def signup_api(
    response: Response,
    user_data: SignupRequest,
    db: AsyncSession = Depends(get_db)
):
    repo = UserRepository()

    try:
        user = UserCreate(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hash_password(user_data.password)
        )

        created_user = await repo.create(db, **user.dict())
        logger.debug(f"User {user_data.username} created")
        
        access_token = jwt_service.create_access_token(user_id=created_user.id)
        refresh_token = jwt_service.create_refresh_token(user_id=created_user.id)

        jwt_service.set_cokies(
            access_token=access_token,
            refresh_token=refresh_token,
            response=response
        )
        
        data = {
          "ok": True,
          "user": {
            "id": created_user.id,
            "username": created_user.username,
            "email": created_user.email
          }
        }
        
        return data
        
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="User already exists")
    except Exception as e:
        await db.rollback()
        logger.error(f"Signup failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/api/v1/auth/login")
async def login_api(
        user_credentials: UserLogin,
        response: Response,
        db: AsyncSession = Depends(get_db),
    ):

    logger.debug(f"Login attempt for: {user_credentials.login}")
    
    stmt = select(User).where(
        or_(
            User.email == user_credentials.login,
            User.username == user_credentials.login
        )
    )
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        logger.warning(f"User not found: {user_credentials.login}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found with this username or email"
        )
    if user.is_deleted:
        logger.warning(f"User {user.username} is deleted")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is deleted"
        )
    logger.debug(f"User found: {user.username}, verifying password")
    try:
        is_valid = argon2.verify(user_credentials.password, user.hashed_password)
        logger.debug(f"Password verification result: {is_valid}")
        if not is_valid:
            logger.warning(f"Invalid password for user: {user.username}")
            raise HTTPException(
                status_code=401,
                detail="Invalid login or password"
            )
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid login or password"
        )

    auth = get_authx()

    access_token = auth.create_access_token(uid=str(user.id))
    refresh_token = auth.create_refresh_token(uid=str(user.id))

    try:
        jwt_service.set_cokies(
            access_token=access_token,
            refresh_token=refresh_token,
            response=response,
        )
    except Exception as e:
        logger.error(f"Error setting cookies: {e}")
        raise HTTPException(
            status_code=500,
            detail="COOKIE_SET_FAILED"
        )
    data = {
        "ok": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }
    return data


# Logout API
@router.post("/api/v1/auth/logout")
async def logout_api(response: Response):
    try:
        response.delete_cookie(
            key=settings.jwt_access_cookie_name,
            path="/",
            samesite="lax",
            secure=False,
        )
        response.delete_cookie(
            key=settings.jwt_refresh_cookie_name,
            path="/",
            samesite="lax",
            secure=False,
        )
    except Exception as e:
        logger.error(f"Error deleting cookies: {e}")
        raise HTTPException(
            status_code=500,
            detail="COOKIE_DELETE_FAILED"
        )
    data = {
        "ok": True
    }
    return data

@router.get("/api/v1/auth/verify")
async def verify_auth(jwt_decoded = Depends(get_current_user)):
    if jwt_decoded["valid"]:
        return {"ok": True}
    if not jwt_decoded["valid"]:
        return HTTPException(status_code=401, detail="Invalid token")
    else:
        return {"ok": False}
