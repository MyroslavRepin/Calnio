"""
Custom Exceptions for Calnio
=============================

Helper functions to raise HTTP exceptions that will automatically
display the appropriate custom error pages.

Usage Examples:
--------------

    from server.utils.exceptions import (
        raise_bad_request,
        raise_unauthorized,
        raise_forbidden,
        raise_not_found,
        raise_rate_limit,
        raise_server_error,
        raise_service_unavailable
    )

    # In your route handlers:

    @app.get("/api/user/{user_id}")
    async def get_user(user_id: int):
        user = await get_user_from_db(user_id)
        if not user:
            raise_not_found(f"User with ID {user_id} not found")
        return user

    @app.post("/api/protected")
    async def protected_route(request: Request):
        if not request.user:
            raise_unauthorized("You must be logged in to access this resource")
        return {"message": "Access granted"}
"""

from fastapi import HTTPException


def raise_bad_request(detail: str = "Bad request"):
    """
    Raise a 400 Bad Request error.
    Displays errors/400.html

    Args:
        detail: Error message to display
    """
    raise HTTPException(status_code=400, detail=detail)


def raise_unauthorized(detail: str = "Authentication required"):
    """
    Raise a 401 Unauthorized error.
    Displays errors/401.html

    Args:
        detail: Error message to display
    """
    raise HTTPException(status_code=401, detail=detail)


def raise_forbidden(detail: str = "Access forbidden"):
    """
    Raise a 403 Forbidden error.
    Displays errors/403.html

    Args:
        detail: Error message to display
    """
    raise HTTPException(status_code=403, detail=detail)


def raise_not_found(detail: str = "Resource not found"):
    """
    Raise a 404 Not Found error.
    Displays errors/404.html

    Args:
        detail: Error message to display
    """
    raise HTTPException(status_code=404, detail=detail)


def raise_rate_limit(detail: str = "Too many requests"):
    """
    Raise a 429 Too Many Requests error.
    Displays errors/429.html

    Args:
        detail: Error message to display
    """
    raise HTTPException(status_code=429, detail=detail)


def raise_server_error(detail: str = "Internal server error"):
    """
    Raise a 500 Internal Server Error.
    Displays errors/500.html

    Args:
        detail: Error message to display
    """
    raise HTTPException(status_code=500, detail=detail)


def raise_service_unavailable(detail: str = "Service temporarily unavailable"):
    """
    Raise a 503 Service Unavailable error.
    Displays errors/503.html

    Args:
        detail: Error message to display
    """
    raise HTTPException(status_code=503, detail=detail)


def raise_custom_error(status_code: int, detail: str):
    """
    Raise a custom HTTP error with any status code.
    Will display errors/error.html with the custom message.

    Args:
        status_code: HTTP status code
        detail: Error message to display
    """
    raise HTTPException(status_code=status_code, detail=detail)

