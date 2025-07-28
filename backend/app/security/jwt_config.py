from authx import AuthX, AuthXConfig


#! JWT Token CONFIG
config = AuthXConfig()
config.JWT_SECRET_KEY = "secret_key"
config.JWT_ACCESS_COOKIE_NAME = "access_token"
config.JWT_REFRESH_COOKIE_NAME = "refresh_token"
config.JWT_TOKEN_LOCATION = ["cookies"]
config.JWT_COOKIE_CSRF_PROTECT = False

security = AuthX(config=config)
