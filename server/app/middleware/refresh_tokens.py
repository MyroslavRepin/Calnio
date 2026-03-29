from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from server.core.jwt_service import JWTService


class AutoRefreshMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, auth, jwt_service: JWTService):
        super().__init__(app)
        self.auth = auth
        self.jwt_service = jwt_service

    async def dispatch(self, request: Request, call_next):
        response = Response("Internal server error", status_code=500)

        try:
            # Попытка проверить access
            await self.auth.access_token_required(request)

        except Exception as e:
            # Если access expired или отсутствует —
            # пробуем refresh
            try:
                # Получаем валидный refresh токен
                refresh_token = await self.auth.get_refresh_token_from_request(request)

                # Получаем subject (это user_id)
                user_id = await self.auth.get_current_subject(request)

                # Создаём новый access
                new_access = self.jwt_service.create_access_token(user_id)

                # Ставим cookie нового access
                response = await call_next(request)
                response.set_cookie(
                    key="access_token",
                    value=new_access,
                    httponly=True,
                    samesite="lax",
                )
                return response

            except Exception:
                # Если и refresh не прошёл — просто идём дальше, auth
                # для защищённых endpoints вернёт 401
                pass

        # Если access валиден или refresh не нужен
        response = await call_next(request)
        return response