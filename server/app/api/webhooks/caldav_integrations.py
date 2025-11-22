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
from server.utils.security.utils import check_if_user_authorized
from server.utils.utils import convert_uuid_no_dashes
from server.app.core.logging_config import logger
from server.services.notion_syncing.webhook_handler import NotionWebhookService

router = APIRouter()

@router.post("/api/v1/integrations/caldav/connect")
async def caldav_integrations(request: Request, db: AsyncSession = Depends(async_get_db)):
    payload = None
    try:
        payload = await request.json()
        logger.info(f"Payload received: {payload}")

        if payload is None:
            logger.error(f"Payload is: {payload}")
            raise Exception("Payload is None")

        caldav_email = payload.get("email")
        specific_password = payload.get("specific_password")
        logger.debug(f"Parsed data: {caldav_email}, {specific_password}")

        data = await check_if_user_authorized(request=request)

        if data["authorized"]:
            user_id = data["user_id"]
            logger.debug(f"Trying to get user with id: {user_id}")
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user = result.scalars().first()

            try:
                logger.debug(f"Trying to save caldav integration for user id: {user_id}")
                user.icloud_email = caldav_email
                user.app_specific_password = specific_password
                await db.commit()
                logger.info(f"Caldav integration saved for user id: {user_id}")
            except Exception as e:
                logger.error(e)
                raise e
        else:
            logger.warning("User is not authorized")
            raise Exception("User is not authorized")

    except Exception as e:
        logger.error(e)
        raise e