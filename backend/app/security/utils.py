from passlib.context import CryptContext
from fastapi.exceptions import HTTPException
from fastapi import Request
from jose import JWTError, jwt  # библиотека для работы с JWT
from backend.app.security.jwt_config import config


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_hash(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


async def access_token_required(request: Request):
    token = request.cookies.get(config.JWT_ACCESS_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        if not config.JWT_SECRET_KEY:
            raise RuntimeError("JWT_SECRET_KEY is not set!")
        payload = jwt.decode(token, config.JWT_SECRET_KEY,
                             algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
