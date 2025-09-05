from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class IgnoreSpecificPathsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, paths=None):
        super().__init__(app)
        self.paths = paths or [
            "/favicon.ico",
            "/.well-known/appspecific/"
        ]

    async def dispatch(self, request: Request, call_next):
        # берём только path без query string
        path = request.url.path.rstrip("/")
        if any(path.startswith(p.rstrip("/")) for p in self.paths):
            return Response(status_code=204)
        return await call_next(request)
