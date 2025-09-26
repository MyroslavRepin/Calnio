"""
APScheduler service for managing periodic sync jobs
"""
import logging
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models.notion_integration import UserNotionIntegration
from backend.app.models.users import User
from backend.app.db.database import AsyncSessionLocal
from backend.app.backround_tasks.notion_sync import notion_sync_background
from notion_client import AsyncClient

logger = logging.getLogger(__name__)


class SyncScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._job_prefix = "notion_sync_"
    
    async def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        logger.info("SyncScheduler started")
        await self._initialize_user_sync_jobs()
    
    async def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("SyncScheduler stopped")
    
    async def _initialize_user_sync_jobs(self):
        """Initialize sync jobs for all users with notion integrations"""
        async with AsyncSessionLocal() as db:
            stmt = select(UserNotionIntegration).join(User)
            result = await db.execute(stmt)
            integrations = result.scalars().all()
            
            for integration in integrations:
                await self.schedule_user_sync(
                    user_id=integration.user_id,
                    sync_interval=integration.sync_interval
                )
                logger.info(f"Scheduled sync job for user {integration.user_id} with interval {integration.sync_interval} minutes")
    
    async def schedule_user_sync(self, user_id: int, sync_interval: int):
        """Schedule or reschedule sync job for a user"""
        job_id = f"{self._job_prefix}{user_id}"
        
        # Remove existing job if it exists
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        
        # Add new job
        self.scheduler.add_job(
            self._sync_user_data,
            trigger=IntervalTrigger(minutes=sync_interval),
            args=[user_id],
            id=job_id,
            name=f"Notion sync for user {user_id}"
        )
        logger.info(f"Scheduled sync job for user {user_id} every {sync_interval} minutes")
    
    async def remove_user_sync(self, user_id: int):
        """Remove sync job for a user"""
        job_id = f"{self._job_prefix}{user_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed sync job for user {user_id}")
    
    async def _sync_user_data(self, user_id: int):
        """Execute sync for a specific user"""
        try:
            async with AsyncSessionLocal() as db:
                # Get user integration
                stmt = select(UserNotionIntegration).where(UserNotionIntegration.user_id == user_id)
                result = await db.execute(stmt)
                integration = result.scalar_one_or_none()
                
                if not integration:
                    logger.warning(f"No integration found for user {user_id}")
                    return
                
                # Create Notion client and sync
                notion = AsyncClient(auth=integration.access_token)
                await notion_sync_background(db=db, notion=notion, user_id=user_id)
                logger.info(f"Completed sync for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error syncing data for user {user_id}: {e}")


# Global scheduler instance
sync_scheduler = SyncScheduler()