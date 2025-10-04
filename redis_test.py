from server.services.webhook_service import sync_webhook_data
import asyncio

asyncio.run(sync_webhook_data())