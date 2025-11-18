from dateutil import parser
import json
from datetime import datetime

import notion_client
from pygments.lexers import q
from sqlalchemy import select
import uuid

from fastapi import APIRouter, Request
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.schemas.notion_pages import NotionTask
from server.db.deps import async_get_db, async_get_db_cm
from server.db.models import UserNotionIntegration, User, UserNotionTask
from server.db.models.enums import SyncStatus
from server.db.redis_client import get_redis
from server.integrations.notion.notion_client import get_notion_client
from server.utils.redis.utils import get_webhook_data, save_webhook_data
from server.services.notion_syncing.webhook_service import sync_webhook_data
from server.utils.utils import convert_uuid_no_dashes
from server.app.core.logging_config import logger
from server.services.notion_syncing.webhook_handler import NotionWebhookService

router = APIRouter()

@router.post("/webhooks/notion")
async def get_notion_response(request: Request, db: AsyncSession = Depends(async_get_db)):
    """
    Handle Notion webhook responses.

    This function processes the incoming payload from Notion webhooks and updates
    the corresponding user, task, or integration data accordingly. It supports
    events like page creation, deletion, and property updates by interacting
    with a database, Redis, and the Notion API.

    Parameters:
    request (Request): The HTTP request containing the webhook payload.
    db (AsyncSession): Dependency-injected asynchronous database session.

    Returns:
    dict: A dictionary containing the response message or error information.

    Raises:
    KeyError: If required keys are missing in the payload.
    ValueError: If invalid data types are encountered in the payload.
    """
    payload = None
    try:
        redis_client = await get_redis()
        payload = await request.json()
        json_payload = json.dumps(payload, indent=4)
        logger.debug(json_payload)

        if not isinstance(payload, dict):
            logger.warning("Webhook payload is not a dict")
            return {"error": "Payload is not a dict"}

        page_id = str(uuid.UUID(payload["entity"]["id"]))

        raw_workspace_id = payload.get("workspace_id")
        workspace_id = str(uuid.UUID(raw_workspace_id))

        event_type = payload["type"]

        logger.debug(f"Webhook received: page_id={page_id}, workspace_id={workspace_id}, event={event_type}")

        if page_id and workspace_id:
            # Getting user by workspace_id (workspace_id is uuid without dashes in db too)
            stmt = (
                select(User)
                .join(UserNotionIntegration)
                .where(UserNotionIntegration.workspace_id == workspace_id)
            )
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                logger.error(f"User not found for workspace_id: {workspace_id}")
                return {"error": "User not found"}

            # Setting page_id and workspace_id in Redis
            data = {
                "user_id": user.id,
                "page_id": page_id,
                "workspace_id": workspace_id,
                "event_type": event_type,
            }

            webhook_handler = NotionWebhookService()

            # Delete
            if event_type == "page.deleted":
                async with async_get_db_cm() as db:
                    update_task = await webhook_handler.handle_page_deleted(db=db, user_id=user.id, page_id=page_id)
                    logger.debug(f"Deleted task: {update_task}")

            # Other operations
            else:
                user_id = user.id
                notion_client = get_notion_client(user.notion_integration.access_token)
                page = await notion_client.pages.retrieve(page_id=page_id)
                notion_page = NotionTask.from_notion(page)
                logger.debug(f"Notion page: {notion_page.__dict__}")

                # Create
                if event_type == "page.created":
                    async with async_get_db_cm() as db:
                        # Todo: This function falls if some of properties are missing, need to handle that
                        create_task = await webhook_handler.handle_page_created(db=db, user=user, user_id=user_id, page_id=page_id)
                        logger.debug(f"Created task: {create_task}")

                # Update
                if event_type == "page.properties_updated":
                    async with async_get_db_cm() as db:
                        update_task = await webhook_handler.handle_page_updated(db=db, user=user, user_id=user_id, page_id=page_id)
                        logger.debug(f"Updated task: {update_task}")
                # Todo: Handle other events as undeleting and archiving

        return {"message": "Notion response", "response": payload}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        logger.debug(f"Webhook data: {json.dumps(payload, indent=4)}")
        return {"error": str(e)}