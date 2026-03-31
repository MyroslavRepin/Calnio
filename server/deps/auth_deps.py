from typing import Any, Optional

from fastapi import Depends, Request, Response, HTTPException
from authx.main import AuthX

from server.core.config import settings
from server.core.jwt_service import JWTService
from server.core.jwt_config import AuthX
from authx import exceptions as authx_exceptions
from server.core.jwt_config import auth
from server.core.logging_config import logger
from jose import JWTError, jwt

auth: AuthX
jwt_service = JWTService()

from fastapi import Request, Response, HTTPException, Depends

async def get_current_user(
    request: Request, response: Response,
):
    """
    Attempts to authenticate the current user using access and refresh tokens. This function first
    tries to validate an access token obtained from the provided request. If the access token
    is invalid or expired, it falls back to using the refresh token to validate the user and
    generate a new access token. On successful validation, relevant user information is returned.
    In case of failure, an error message is returned.

    :param request: The incoming HTTP request containing cookies or headers that may include
        access and refresh tokens.
    :type request: Request
    :param response: The outgoing HTTP response where a new access token may be set in cookies.
    :type response: Response
    :return: A dictionary indicating whether the authentication was successful (`"valid": True`)
        along with user details, or an error message if authentication failed (`"valid": False`,
        `"error": str`).
    :rtype: dict
    """
    # Attempts access token authentication; falls back to refresh
    try:
        access_token = await auth.get_access_token_from_request(request)

        payload = auth.verify_token(access_token, verify_csrf=False)
        logger.debug(f"Access token is valid: {payload}")

        if payload.type != "access":
            raise Exception("Not an access token")

        return {"valid": True, "user_id": payload.sub, "payload": payload}

    except Exception as e:
        logger.debug(f"Access token is invalid, attempting refresh: {e}")
        try:
            refresh_token = await auth.get_refresh_token_from_request(request)
        except Exception as e:
            raise HTTPException(status_code=401, detail="Refresh token not found in cookies or headers") from e
        try:
            payload = auth.verify_token(refresh_token, verify_csrf=False)
            logger.debug(f"Refresh token is valid: {payload}")
            new_access_token = auth.create_access_token(uid=payload.sub)
            logger.debug(f"Generated new access token")
            response.set_cookie(
                key=settings.jwt_access_cookie_name,
                value=new_access_token,
                httponly=True,
                samesite="lax",
            )
            logger.debug("Cookies set")
            return {"valid": True, "user_id": payload.sub, "payload": payload}
        except Exception as e:
            return { "valid": False, "error": str(e)}
