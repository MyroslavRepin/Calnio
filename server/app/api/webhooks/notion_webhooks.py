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
from server.services.notion_syncing.webhook_service import sync_webhook_data
from server.utils.utils import convert_uuid_no_dashes
from server.app.core.logging_config import logger

router = APIRouter()

@router.post("/webhooks/notion/")
async def get_notion_response(request: Request, db: AsyncSession = Depends(async_get_db)):
    payload = None
    try:
        redis_client = await get_redis()
        payload = await request.json()

        if not isinstance(payload, dict):
            logger.warning("⚠️ Webhook payload is not a dict")
            return {"error": "Payload is not a dict"}

        raw_page_id = uuid.UUID(payload["entity"]["id"])
        page_id = raw_page_id.hex

        raw_workspace_id = uuid.UUID(payload.get("workspace_id"))
        workspace_id = raw_workspace_id.hex

        event_type = payload["type"]

        logger.debug(f"📥 Webhook received: page_id={page_id}, workspace_id={workspace_id}, event={event_type}")

        # Saving data to Redis
        if page_id and workspace_id:
            # Getting user by workspace_id (workspace_id is uuid without dashes in db too)
            stmt = (
                select(User)
                .join(UserNotionIntegration)
                .where(UserNotionIntegration.workspace_id == workspace_id)
            )
            result = await db.execute(stmt)
            user = result.scalars().first()

            if not user:
                logger.error(f"❌ User not found for workspace_id: {workspace_id}")
                return {"error": "User not found"}

            # Setting page_id and workspace_id in Redis
            data = {
                "user_id": user.id,
                "page_id": page_id,
                "workspace_id": workspace_id,
                "event_type": event_type,
            }

            await save_webhook_data(user_id=user.id, redis=redis_client, data=data)
            logger.debug(f"💾 Webhook data saved to Redis for user_id={user.id}")

        await sync_webhook_data()

        return {"message": "Notion response", "response": payload}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        logger.debug(f"Webhook data: {json.dumps(payload, indent=4)}")
        return {"error": str(e)}