from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class IgnorePathLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/frontend/static/js/api.js"]:
            return await call_next(request)  # Не логируем
        return await call_next(request)
