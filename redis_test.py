from server.services.notion_syncing.webhook_service import sync_webhook_data
import asyncio

asyncio.run(sync_webhook_data())