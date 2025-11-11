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
from server.db.deps import async_get_db
from server.db.models import UserNotionIntegration, User, UserNotionTask
from server.db.models.enums import SyncStatus
from server.db.redis_client import get_redis
from server.integrations.notion.notion_client import get_notion_client
from server.utils.redis.utils import get_webhook_data, save_webhook_data
from server.services.notion_syncing.webhook_service import sync_webhook_data
from server.utils.utils import convert_uuid_no_dashes
from server.app.core.logging_config import logger

router = APIRouter()

@router.post("/webhooks/notion/")
async def get_notion_response(request: Request, db: AsyncSession = Depends(async_get_db)):
    payload = None
    try:
        logger.debug(json.dumps(payload, indent=4))
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

            if event_type == "page.deleted":
                # Todo: get the task from db and set deleted_at
                stmt = select(UserNotionTask).where(
                    UserNotionTask.user_id==user.id,
                    UserNotionTask.notion_page_id==page_id
                )
                result = await db.execute(stmt)
                task = result.scalar_one_or_none()

                if not task:
                    logger.warning(f"Task: {task.id} not found in database")
                    return {"error": "Task not found"}

                task.deleted = True
                task.deleted_at = datetime.now(datetime.timezone.utc)

                await db.commit()
                await db.refresh(task)

            user_id = user.id

            notion_client = get_notion_client(user.notion_integration.access_token)
            page = await notion_client.pages.retrieve(page_id=page_id)
            notion_page = NotionTask.from_notion(page)

            if event_type == "page.created":
                # Todo: if there are no tasks with same notion_page_id -> Create new page
                stmt = select(UserNotionTask).where(
                    UserNotionTask.user_id==user.id,
                    UserNotionTask.notion_page_id==page_id
                )
                result = await db.execute(stmt)
                task = result.scalar_one_or_none()

                if task:
                    logger.warning(f"Task: {task.id} already exists in database")
                    return {"error": "Task already exists"}
                if not task:
                    try:
                        logger.debug(f"Creating new task for page_id: {page_id}")
                        start_date = parser.isoparse(notion_page.start_date)
                        end_date = parser.isoparse(notion_page.end_date)

                        new_task = UserNotionTask(
                            user_id=user_id,
                            notion_page_id=page_id,
                            notion_url=notion_page.notion_page_url,
                            title=notion_page.title,
                            description=notion_page.description,
                            status=notion_page.status,
                            priority=notion_page.priority,
                            select_option=notion_page.select_option,
                            done=notion_page.done,
                            start_date=start_date,
                            end_date=end_date,
                            sync_source="notion",
                            caldav_id="pending",
                            last_modified_source="notion",
                            sync_status=SyncStatus.pending,
                            deleted=False,
                        )
                        db.add(new_task)
                        await db.commit()
                        await db.refresh(new_task)
                    except Exception as e:
                        logger.error(f"Error creating new task: {e}")
                        return {"error": str(e)}


            if event_type == "page.properties_updated":
                # Todo: get the page and update properties
                ...
        # await sync_webhook_data()

        return {"message": "Notion response", "response": payload}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        logger.debug(f"Webhook data: {json.dumps(payload, indent=4)}")
        return {"error": str(e)}