from datetime import timedelta

from authx import AuthX, AuthXConfig

from server.core.config import settings

config = AuthXConfig()

config.JWT_ALGORITHM = "HS256"
config.JWT_SECRET_KEY = settings.jwt_secret_key
config.JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
config.JWT_ACCESS_COOKIE_NAME = settings.jwt_access_cookie_name
config.JWT_REFRESH_COOKIE_NAME = settings.jwt_refresh_cookie_name
config.JWT_TOKEN_LOCATION = ["cookies"]
config.JWT_COOKIE_CSRF_PROTECT=False

auth = AuthX(config)
def get_authx():
    return auth

# auth.handle_errors(app)  # Register error handlers for proper responses
