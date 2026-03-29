from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent  # папка с settings.py

class Settings(BaseSettings):
    """Minimal settings for Reflectly project with async Postgres"""

    db_host: str = Field(default="db")
    db_user: str = Field(default="root")
    db_password: str = Field(default="secretKey")
    db_name: str = Field(default="reflectly")
    db_port: int = Field(default=5432)
    db_url_full: str

    jwt_secret_key: str = Field(default="secretKey")
    jwt_access_cookie_name: str = Field(default="access_token")
    jwt_refresh_cookie_name: str = Field(default="refresh_token")
    jwt_access_token_expire_seconds: int = Field(default=30)
    jwt_token_location: list[str]
    jwt_cookie_csrf_protect: bool = Field(default=False)
    jwt_access_token_expires_seconds: int = Field(default=30)
    jwt_algorithm: str = Field(default="HS256")

    server_host: str = Field(default="0.0.0.0")
    server_port: int = Field(default=8080)
    server_debug: bool = Field(default=True)
    server_reload: bool = Field(default=True)

    cloudflared_tunnel_token: str
    cloudflared_tunnel_name: str

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

    @property
    def database_url(self) -> str:
        """Async database URL for SQLAlchemy + asyncpg"""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()