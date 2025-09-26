"""
Scheduler service for managing background synchronization tasks.
"""
import logging
from typing import Dict, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio

from backend.app.db.database import AsyncSessionLocal
from backend.app.models.users import User
from backend.app.models.notion_integration import UserNotionIntegration
from backend.app.backround_tasks.notion_sync import async_create_task
from backend.app.tools.notion.utils import get_all_ids
from notion_client import AsyncClient

logger = logging.getLogger(__name__)


class SyncScheduler:
    """Manages scheduled synchronization tasks for users."""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.user_jobs: Dict[int, str] = {}  # user_id -> job_id mapping
        
    def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Sync scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Sync scheduler shutdown")
    
    def add_user_sync_job(self, user_id: int, sync_interval_minutes: int):
        """Add or update a sync job for a user."""
        job_id = f"sync_user_{user_id}"
        
        # Remove existing job if it exists
        if user_id in self.user_jobs:
            self.scheduler.remove_job(self.user_jobs[user_id])
        
        # Add new job
        try:
            self.scheduler.add_job(
                func=self._sync_user_wrapper,
                trigger=IntervalTrigger(minutes=sync_interval_minutes),
                id=job_id,
                args=[user_id],
                replace_existing=True,
                max_instances=1
            )
            self.user_jobs[user_id] = job_id
            logger.info(f"Added sync job for user {user_id} with interval {sync_interval_minutes} minutes")
        except Exception as e:
            logger.error(f"Failed to add sync job for user {user_id}: {e}")
    
    def remove_user_sync_job(self, user_id: int):
        """Remove sync job for a user."""
        if user_id in self.user_jobs:
            try:
                self.scheduler.remove_job(self.user_jobs[user_id])
                del self.user_jobs[user_id]
                logger.info(f"Removed sync job for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to remove sync job for user {user_id}: {e}")
    
    def _sync_user_wrapper(self, user_id: int):
        """Wrapper to run async sync function in sync context."""
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(self._sync_user_async(user_id))
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Sync job failed for user {user_id}: {e}")
    
    async def _sync_user_async(self, user_id: int):
        """Perform synchronization for a specific user."""
        async with AsyncSessionLocal() as db:
            try:
                # Get user and their notion integration
                stmt = select(User).where(User.id == user_id)
                result = await db.execute(stmt)
                user = result.scalar_one_or_none()
                
                if not user or not user.notion_integration:
                    logger.warning(f"User {user_id} or their Notion integration not found")
                    return
                
                integration = user.notion_integration
                if not integration.access_token:
                    logger.warning(f"No access token for user {user_id}")
                    return
                
                # Initialize Notion client
                notion = AsyncClient(auth=integration.access_token)
                
                # Get all page IDs from Notion
                page_ids = await get_all_ids(notion)
                logger.info(f"Found {len(page_ids)} pages for user {user_id}")
                
                # Sync each page (simplified version of existing logic)
                for page_id in page_ids:
                    try:
                        page = await notion.pages.retrieve(page_id=page_id)
                        
                        # Extract basic page info
                        title = "Untitled"
                        if page.get("properties"):
                            # Try to get title from different possible title properties
                            for prop_name, prop_data in page["properties"].items():
                                if prop_data.get("type") == "title" and prop_data.get("title"):
                                    title = "".join([t.get("plain_text", "") for t in prop_data["title"]])
                                    break
                        
                        # Create or update task
                        await async_create_task(
                            db=db,
                            user_id=user_id,
                            title=title,
                            notion_page_id=page_id,
                            notion_url=page.get("url", ""),
                            description=None,
                            task_date=None,
                            status=None,
                            done=False,
                            priority=None,
                            select_option=None
                        )
                        
                    except Exception as e:
                        logger.error(f"Failed to sync page {page_id} for user {user_id}: {e}")
                        continue
                
                await db.commit()
                logger.info(f"Completed sync for user {user_id}")
                
            except Exception as e:
                logger.error(f"Database error during sync for user {user_id}: {e}")
                await db.rollback()


# Global scheduler instance
sync_scheduler = SyncScheduler()