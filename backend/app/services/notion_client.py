from notion_client import AsyncClient

def get_notion_client(token: str):
    return AsyncClient(auth=token)