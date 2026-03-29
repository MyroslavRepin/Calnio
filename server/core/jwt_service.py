import jose.jwt
from fastapi import Request, Response, HTTPException
from authx.exceptions import AuthXException
from jose import JWTError, jwt


from server.core.config import settings
from server.core.jwt_config import auth
from server.core.logging_config import logger


class JWTService:
    """
    Provides functionality to create JSON Web Tokens (JWT) for user authentication.

    This class helps in generating JWTs for secure user authentication. It uses
    user-specific data to generate tokens that can be utilized to access protected
    APIs or resources. The tokens are valid for a specific duration and provide
    a mechanism to verify user identity.

    :ivar secret_key: Secret key used for signing the JWT.
    :type secret_key: str
    :ivar algorithm: Algorithm used for encoding the JWT.
    :type algorithm: str
    :ivar expiration_time: Time duration (in seconds) for which the token is valid.
    :type expiration_time: int
    """

    def create_access_token(self, user_id: int) -> str:
        """
        Generate an access token for a given user.

        This method creates a secure token for user authentication,
        uniquely tied to the provided user ID. The token can be
        used for session management and validating user identity
        in the system.

        :param user_id: The unique identifier for the user.
        :type user_id: int
        :return: A string representing the generated access token.
        :rtype: str
        """
        return auth.create_access_token(uid=str(user_id))

    def create_refresh_token(self, user_id: int) -> str:
        """
        Generates a refresh token for the specified user.

        This function generates a new refresh token associated with the provided user
        identifier. The token can be used for authentication purposes in further
        interactions with the system.

        :param user_id: The unique identifier of the user for whom the refresh token
                        needs to be generated.
        :return: A string representing the newly"""
        return auth.create_refresh_token(uid=str(user_id))

    def logout(self, response: Response):
        """
        Logs the user out by unsetting authentication cookies.

        This method clears cookies associated with authentication in the provided
        response object.

        :param response: The HTTP response object where cookies will be unset.
        :type response: Response
        :return: None
        """
        auth.unset_cookies(response)

    def set_cokies(self, access_token, refresh_token, response: Response):
        """
        Sets authentication cookies in the HTTP response.

        This method sets the access and refresh tokens as cookies in the provided
        HTTP response object. These cookies are used for maintaining user sessions
        and authentication.

        :param access_token: The access token to be set as a cookie.
        :type access_token: str
        :param refresh_token: The refresh token to be set as a cookie.
        :type refresh_token: str
        :param response: The HTTP response object where cookies will be set.
        :type response: Response
        :return: None
        """

        response.set_cookie(
            key=settings.jwt_access_cookie_name,
            value=access_token,
            httponly=True,
            path="/",
            samesite="lax",
        )
        response.set_cookie(
            key=settings.jwt_refresh_cookie_name,
            value=refresh_token,
            httponly=True,
            path="/",
            samesite="lax",
        )

        logger.debug("Cookies set")
        return response

    def decode_token(self, token: str) -> dict:
        decoded_token = jose.jwt.decode(token=token, key=settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return {decoded_token}
