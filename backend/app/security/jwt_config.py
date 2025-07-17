from authx import AuthX, AuthXConfig


#! JWT Token CONFIG
config = AuthXConfig()
config.JWT_SECRET_KEY = "secret_key"
config.JWT_ACCESS_COOKIE_NAME = "acces_token"
config.JWT_TOKEN_LOCATION = ["cookies"]

security = AuthX(config=config)
