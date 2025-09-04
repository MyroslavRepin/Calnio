from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pathlib import Path

# Загрузить .env перед тем, как объявлять настройки
dotenv_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path, override=True)


class Settings(BaseSettings):
    env: str = "local"
    database_url_local: str
    database_url_prod: str
    oauth_client_id: str
    oauth_client_secret: str
    notion_redirect_uri: str

    @property
    def database_url(self) -> str:
        return self.database_url_prod if self.env == "prod" else self.database_url_local

    @property
    def redirect_uri(self) -> str:
        return (
            "https://calnio.com/oauth/callback"
            if self.env == "prod"
            else "http://localhost:8000/oauth/callback"
        )

    class Config:
        env_file = str(Path(__file__).resolve(
        ).parents[3] / ".env")  # путь к .env


settings = Settings()
