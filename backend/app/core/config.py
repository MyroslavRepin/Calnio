from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pathlib import Path

# Загрузить .env перед тем, как объявлять настройки
dotenv_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(dotenv_path, override=True)


class Settings(BaseSettings):
    env: str
    db: str
    https: bool
    notion_send_data_env: str

    database_url_prod: str
    database_url_local: str

    notion_oauth_client_id_prod: str
    notion_oauth_client_id_local: str

    notion_oauth_secret_prod: str
    notion_oauth_secret_local: str

    notion_redirect_prod: str
    notion_redirect_local: str
    notion_redirect_local_https: str

    oauth_url_prod: str
    oauth_url_local: str

    @property
    def database_url(self):
        if self.env == "prod":
            if self.db == "local":
                return self.database_url_local
        else:
            return self.database_url_local

    @property
    def notion_redirect_uri(self):
        if self.env == "prod":
            if self.notion_send_data_env == "prod":
                return self.notion_redirect_prod
            else:
                return self.notion_redirect_local

        else:
            if self.https == "True":
                if self.notion_send_data_env == "prod":
                    return self.notion_redirect_prod
                else:
                    return self.notion_redirect_local_https
            else:
                if self.notion_send_data_env == "prod":
                    return self.notion_redirect_prod
                else:
                    return self.notion_redirect_local

    @property
    def notion_secert(self):
        if self.env == "prod":
            return self.notion_oauth_secret_prod
        else:
            return self.notion_oauth_secret_local

    @property
    def notion_client_id(self):
        if self.env == "prod":
            return self.notion_oauth_client_id_prod
        else:
            return self.notion_oauth_client_id_local

    @property
    def notion_oauth_url(self):
        if self.env == "prod":
            return self.oauth_url_prod
        else:
            return self.oauth_url_local

    class Config:
        env_file = str(Path(__file__).resolve(
        ).parents[3] / ".env")  # путь к .env
        env_file_encoding = "utf-8"


settings = Settings()  # pyright: ignore[reportCallIssue]
