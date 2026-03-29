from fastapi import HTTPException, Request

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.repositories.users import UserRepository
from server.db.sessions import get_db
from server.deps.auth_deps import get_current_user
from server.core.logging_config import logger
from server.deps.schemas.users_schemes import UpdateUser, UserResponse
from server.utils.security.auth import hash_password
from sqlalchemy.exc import IntegrityError

router = APIRouter()

user_repo = UserRepository()

@router.patch("/api/v1/users/me", response_model=UserResponse)
async def update_user(
    user_data: UpdateUser,
    db: AsyncSession = Depends(get_db),
    jwt_decoded: dict = Depends(get_current_user),
):
    user_id = int(jwt_decoded["user_id"])
    logger.debug(f"Updating user {user_id}")
    logger.debug(f"Received user_data model: {user_data.model_dump()}")

    update_data = user_data.model_dump(exclude_unset=True, exclude_none="yes")

    if "password" in update_data:
        update_data["hashed_password"] = hash_password(
            plain_password=update_data.pop("password")
        )
    logger.debug(f"Updating user with data: {update_data}")
    try:
        user = await user_repo.update(db, user_id, **update_data)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Email or username already exists")
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/v1/users/me", response_model=UserResponse)
async def get_current_user(jwt_decoded: str = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user_id = int(jwt_decoded["user_id"])
    user = await user_repo.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user