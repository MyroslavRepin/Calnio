from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class IgnoreSpecificPathsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/.well-known/appspecific/com.chrome.devtools.json":
            # просто вернуть 404 без логов
            from starlette.responses import Response
            return Response(status_code=404)
        response = await call_next(request)
        return response
