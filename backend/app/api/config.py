"""
Configuration API endpoints
"""
import logging
from fastapi import APIRouter, Request, Form, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.crud.users import async_get_by_id
from backend.app.db.deps import async_get_db
from backend.app.security.utils import check_if_user_authorized
from backend.app.models.notion_integration import UserNotionIntegration
from backend.app.services.scheduler import sync_scheduler

router = APIRouter()

@router.post("/api/config/sync-interval")
async def update_sync_interval(
    request: Request,
    sync_interval: int = Form(...),
    db: AsyncSession = Depends(async_get_db)
):
    """Update sync interval for a user"""
    data = await check_if_user_authorized(request)
    user_id = data["user_id"]
    if not data["authorized"]:
        raise HTTPException(status_code=401, detail="Not authorized")
    
    # Validate sync_interval
    if sync_interval < 5 or sync_interval > 1440:  # 5 minutes to 24 hours
        raise HTTPException(status_code=400, detail="Sync interval must be between 5 and 1440 minutes")
    
    # Get user's notion integration
    stmt = select(UserNotionIntegration).where(UserNotionIntegration.user_id == user_id)
    result = await db.execute(stmt)
    integration = result.scalar_one_or_none()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Notion integration not found")
    
    # Update sync interval
    integration.sync_interval = sync_interval
    await db.commit()
    
    # Reschedule sync job
    await sync_scheduler.schedule_user_sync(user_id=user_id, sync_interval=sync_interval)
    
    logging.info(f"Updated sync interval for user {user_id} to {sync_interval} minutes")
    
    return RedirectResponse("/dashboard", status_code=302)