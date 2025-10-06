from notion_client import AsyncClient
from server.app.core.config import settings


class NotionService:
    def __init__(self, token: str = settings.notion_oauth_secret_prod):
        self.client = AsyncClient(auth=token)

    async def query_database(self, database_id: str, **kwargs):
        """Запрос к базе данных Notion"""
        return await self.client.databases.query(database_id=database_id, **kwargs)

    async def get_page(self, page_id: str):
        """Получить страницу по ID"""
        return await self.client.pages.retrieve(page_id=page_id)

    async def create_page(self, parent_id: str, properties: dict):
        """Создать страницу"""
        return await self.client.pages.create(parent={"database_id": parent_id}, properties=properties)


# Глобальный экземпляр для использования в других модулях
notion_service = NotionService()
