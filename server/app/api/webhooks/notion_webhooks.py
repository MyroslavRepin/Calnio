import json

from sqlalchemy import select
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.deps import async_get_db
from server.db.models import UserNotionIntegration, User
from server.db.redis_client import get_redis
from server.utils.redis.utils import save_webhook_data
from server.services.notion_syncing.webhook_service import sync_webhook_data
from server.app.core.logging_config import logger

router = APIRouter()


def _safe_get(obj: Any, key: str, default: Any = None, field_path: str = "") -> tuple[Any, Optional[str]]:
    """
    Safely extract a field from an object using .get() and return value + optional warning message.

    Args:
        obj: The object to extract from (dict, or None)
        key: The key to look up
        default: Default value if missing
        field_path: Dotted path for logging (e.g., "payload.data.updated_properties")

    Returns:
        Tuple of (value, warning_message)
        - value: The extracted value or default if missing
        - warning_message: None if found, or a detailed message if missing/None
    """
    if obj is None:
        msg = f"Cannot extract '{key}' from {field_path}: parent object is None"
        logger.warning(f"Field extraction warning: {msg}")
        return default, msg

    if not isinstance(obj, dict):
        msg = f"Cannot extract '{key}' from {field_path}: parent is {type(obj).__name__}, not dict"
        logger.warning(f"Field extraction warning: {msg}")
        return default, msg

    if key not in obj:
        msg = f"Field '{key}' missing from {field_path}; available keys: {list(obj.keys())}"
        logger.warning(f"Field extraction warning: {msg}")
        return default, msg

    value = obj.get(key, default)
    if value is None:
        msg = f"Field '{key}' in {field_path} is None"
        logger.warning(f"Field extraction warning: {msg}")
        return default, msg

    logger.debug(f"Successfully extracted '{key}' from {field_path}")
    return value, None

@router.post("/webhooks/notion/")
async def get_notion_response(request: Request, db: AsyncSession = Depends(async_get_db)):
    """
    Handle Notion webhook payloads for page.created, page.properties_updated, and page.deleted events.

    Safely extracts all fields using .get() to avoid NoneType errors.
    Logs exactly which fields are missing or None.
    Stores page_id and workspace_id in Redis.
    Gets the User by workspace_id (UUID stored as string without dashes in DB).
    Calls sync_webhook_data() at the end.
    """
    payload = None
    redis_client = None
    extracted_fields = {}  # Track which fields we successfully extracted
    missing_fields = {}  # Track which fields were missing

    logger.info("=" * 80)
    logger.info("Notion webhook request received")
    logger.info("=" * 80)

    try:
        # ============================================================================
        # 1. Parse JSON payload
        # ============================================================================
        try:
            payload = await request.json()
            logger.debug(f"Raw webhook payload: {json.dumps(payload, indent=2)}")
        except Exception as e:
            logger.error(f"Failed to parse JSON from request body: {e}")
            return {"error": "Invalid JSON payload"}

        if not isinstance(payload, dict):
            logger.error(f"Webhook payload is not a dict; got {type(payload).__name__}")
            return {"error": "Payload must be a dict"}

        logger.info(f"Payload keys received: {list(payload.keys())}")

        # ============================================================================
        # 2. Extract event type (page.created, page.properties_updated, page.deleted)
        # ============================================================================
        event_type, warning_msg = _safe_get(payload, "type", default="unknown", field_path="payload.type")
        if warning_msg:
            missing_fields["type"] = warning_msg
        extracted_fields["type"] = event_type
        logger.info(f"Event type: {event_type}")

        # ============================================================================
        # 3. Extract entity and entity.id (the page ID)
        # ============================================================================
        entity, entity_warning = _safe_get(payload, "entity", default={}, field_path="payload.entity")
        if entity_warning:
            missing_fields["entity"] = entity_warning
            logger.error("Cannot proceed without 'entity' field; returning error")
            return {"error": "Entity field missing or None"}

        entity_id, entity_id_warning = _safe_get(entity, "id", default=None, field_path="payload.entity.id")
        if entity_id_warning:
            missing_fields["entity.id"] = entity_id_warning
            logger.error("Cannot proceed without 'entity.id' field; returning error")
            return {"error": "Entity ID missing or None"}

        # Convert entity_id (UUID string) to hex format (no dashes)
        try:
            page_id = uuid.UUID(entity_id).hex
            logger.info(f"Page ID (entity.id): {entity_id} → hex: {page_id}")
            extracted_fields["page_id"] = page_id
        except Exception as e:
            logger.error(f"Failed to parse entity_id as UUID: {entity_id}, error: {e}")
            return {"error": f"Invalid entity ID format: {entity_id}"}

        # ============================================================================
        # 4. Extract workspace_id
        # ============================================================================
        workspace_id_raw, workspace_warning = _safe_get(payload, "workspace_id", default=None, field_path="payload.workspace_id")
        if workspace_warning:
            missing_fields["workspace_id"] = workspace_warning
            logger.error("Cannot proceed without 'workspace_id' field; returning error")
            return {"error": "Workspace ID missing or None"}

        # Convert workspace_id (UUID string) to standard UUID string format (with dashes)
        try:
            workspace_id = str(uuid.UUID(workspace_id_raw))
            logger.info(f"Workspace ID: {workspace_id_raw} → standard: {workspace_id}")
            extracted_fields["workspace_id"] = workspace_id
        except Exception as e:
            logger.error(f"Failed to parse workspace_id as UUID: {workspace_id_raw}, error: {e}")
            return {"error": f"Invalid workspace ID format: {workspace_id_raw}"}

        # ============================================================================
        # 5. Extract "data" and "updated_properties" if they exist
        #    (page.created may not have these; page.properties_updated should)
        # ============================================================================
        data_obj, data_warning = _safe_get(payload, "data", default={}, field_path="payload.data")
        if data_warning:
            logger.info(f"'data' field note: {data_warning} (this is normal for page.created)")
            missing_fields["data"] = data_warning

        if event_type == "page.properties_updated":
            updated_properties, updated_props_warning = _safe_get(
                data_obj, "updated_properties", default=[], field_path="payload.data.updated_properties"
            )
            if updated_props_warning:
                logger.warning(f"'updated_properties' missing for page.properties_updated event: {updated_props_warning}")
                missing_fields["data.updated_properties"] = updated_props_warning
            else:
                # updated_properties is a LIST of property names, e.g., ["title", "status"]
                logger.info(f"Updated properties: {updated_properties if isinstance(updated_properties, list) else 'Invalid format'}")
                extracted_fields["updated_properties"] = updated_properties
        else:
            logger.info(f"Event type '{event_type}' does not use 'updated_properties'; skipping")
            extracted_fields["updated_properties"] = None

        # ============================================================================
        # 6. Initialize Redis client
        # ============================================================================
        try:
            redis_client = await get_redis()
            logger.debug("Redis client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            return {"error": "Redis connection failed"}

        # ============================================================================
        # 7. Query database for User by workspace_id
        # ============================================================================
        workspace_id = str(workspace_id_raw)
        try:
            logger.debug(f"Querying database for User with workspace_id={workspace_id}")
            stmt = (
                select(User)
                .join(UserNotionIntegration)
                .where(UserNotionIntegration.workspace_id == workspace_id)
            )
            result = await db.execute(stmt)
            user = result.scalars().first()

            if not user:
                logger.error(f"User not found for workspace_id={workspace_id}")
                return {"error": "User not found"}

            logger.info(f"User found: user_id={user.id}, email={getattr(user, 'email', 'N/A')}")
            extracted_fields["user_id"] = user.id
        except Exception as e:
            logger.error(f"Database query failed for workspace_id={workspace_id}: {e}", exc_info=True)
            return {"error": "Database query error"}

        # ============================================================================
        # 8. Prepare data for Redis
        # ============================================================================
        redis_data = {
            "user_id": user.id,
            "page_id": page_id,
            "workspace_id": workspace_id,
            "event_type": event_type,
            "payload_keys": list(payload.keys()),
            "extracted_fields": extracted_fields,
            "missing_fields": missing_fields,
        }

        logger.debug(f"Redis data prepared: {json.dumps(redis_data, indent=2, default=str)}")

        # ============================================================================
        # 9. Save webhook data to Redis
        # ============================================================================
        try:
            await save_webhook_data(user_id=user.id, redis=redis_client, data=redis_data)
            logger.info(f"Webhook data saved to Redis for user_id={user.id}")
        except Exception as e:
            logger.error(f"Failed to save webhook data to Redis: {e}", exc_info=True)
            # Don't return error; continue to sync attempt

        # ============================================================================
        # 10. Trigger webhook sync
        # ============================================================================
        try:
            logger.info(f"Triggering sync_webhook_data() for event_type={event_type}")
            await sync_webhook_data(user_id=user.id)  # Pass user_id to fetch correct webhook data
            logger.info("Webhook sync completed successfully")
        except Exception as e:
            logger.error(f"Webhook sync failed: {e}", exc_info=True)
            # Return error but still indicate we processed it
            return {
                "message": "Webhook received and queued, but sync failed",
                "error": str(e),
                "event_type": event_type,
            }

        # ============================================================================
        # 11. Success response
        # ============================================================================
        logger.info("=" * 80)
        logger.info("Webhook processed successfully")
        logger.info("=" * 80)
        return {
            "message": "Notion webhook processed successfully",
            "event_type": event_type,
            "page_id": page_id,
            "workspace_id": workspace_id,
            "user_id": user.id,
        }

    except Exception as e:
        logger.error(f"Unexpected error processing webhook: {e}", exc_info=True)
        if payload is not None:
            logger.debug(f"Payload state at error: {json.dumps(payload, indent=2, default=str)}")
        logger.info("=" * 80)
        return {"error": f"Unexpected error: {str(e)}"}
