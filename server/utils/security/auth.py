from http.client import HTTPException
from fastapi import Request, Response
from jose.exceptions import JWTError
from jose import jwt

from server.core.config import settings
from server.core.jwt_config import auth


def hash_password(plain_password: str) -> str:
    """
    Hashes a plain password using bcrypt algorithm for secure storage. The function
    utilizes the `passlib` library's CryptContext to handle the hashing operation,
    ensuring that the password is stored in a non-reversible and secure manner.

    :param plain_password: The plain text password to be hashed.
    :type plain_password: str
    :return: The hashed password.
    :rtype: str
    """
    from passlib.context import CryptContext

    if len(plain_password.encode("utf-8")) > 72:
        raise ValueError("Password length exceeds maximum limit of 72 bytes for bcrypt.")

    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
    return pwd_context.hash(plain_password)

