import json
from sqlalchemy import select
import uuid

from fastapi import APIRouter, Request
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.deps import async_get_db
from server.db.models import UserNotionIntegration, User
from server.db.redis_client import get_redis
from server.utils.redis.utils import get_webhook_data, save_webhook_data
from server.services.webhook_service import sync_webhook_data

router = APIRouter()

@router.post("/webhooks/notion/")
async def get_notion_response(request: Request, db: AsyncSession = Depends(async_get_db)):
    redis_client = await get_redis()
    payload = await request.json()

    if not isinstance(payload, dict):
        return {"error": "Payload is not a dict"}

    print(">>> Notion webhook collected")

    raw_page_id = uuid.UUID(payload["entity"]["id"])
    page_id = raw_page_id.hex

    workspace_id = payload.get("workspace_id")

    print(f">>> Debug info: page_id: {page_id} | workspace_id: {workspace_id}")

    # Saving data to Redis
    if page_id and workspace_id:
        # Statement for query db
        stmt = (
            select(User)
            .join(UserNotionIntegration)
            .where(UserNotionIntegration.workspace_id == workspace_id)
        )
        result = await db.execute(stmt)
        user = result.scalars().first()

        # Setting page_id and workspace_id in Redis
        data = {
            "user_id": user.id,
            "page_id": page_id,
            "workspace_id": workspace_id
        }
        await save_webhook_data(redis=redis_client, data=data, user_id=user.id)

        webhook_data = await get_webhook_data(user_id=user.id, redis=redis_client)
        print(">>> Webhook data:", webhook_data)

    await sync_webhook_data()

    return {"message": "Notion response", "response": payload}