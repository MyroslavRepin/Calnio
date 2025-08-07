from backend.app.security.jwt_config import security, config
from fastapi import Request, Response, HTTPException, status
from passlib.context import CryptContext
from fastapi.exceptions import HTTPException
from fastapi import Request
from jose import JWTError, jwt
from backend.app.security.jwt_config import config


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_hash(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


async def access_token_required(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    token = auth_header[len("Bearer "):]

    try:
        if not config.JWT_SECRET_KEY:
            raise RuntimeError("JWT_SECRET_KEY is not set!")

        payload = jwt.decode(token, config.JWT_SECRET_KEY,
                             algorithms=["HS256"])
        return payload  # payload может содержать user_id в "sub"
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


async def refresh_access_token(request: Request, response: Response) -> dict:
    try:
        # Проверяем и извлекаем payload из refresh_token cookie
        refresh_payload = await security.refresh_token_required(request)

        # Создаём новый access токен на основе user_id из payload
        new_access_token = security.create_access_token(refresh_payload.sub)

        response.delete_cookie(
            key=config.JWT_ACCESS_COOKIE_NAME,
            path="/",
            samesite="lax",
            secure=False,
        )
        response.set_cookie(
            key=config.JWT_ACCESS_COOKIE_NAME,
            value=new_access_token,
            httponly=True,
            samesite="lax",
            secure=False,  # In prode should be True (https)
            path="/",
        )

        return {"sub": refresh_payload.sub}
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=401, detail="Invalid refresh token or expired")
