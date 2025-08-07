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

    @property
    def database_url(self) -> str:
        return self.database_url_prod if self.env == "prod" else self.database_url_local

    class Config:
        env_file = str(Path(__file__).resolve(
        ).parents[3] / ".env")  # путь к .env


settings = Settings()
