from curses import wrapper

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.core.config import settings
from backend.app.db.deps import async_get_db
from backend.app.models import User
from backend.app.services.crud.tasks import async_create_task
from backend.app.services.notion_client import get_notion_client
from backend.app.services.notion_sync import notion_sync_background

# Scheduler config, can be extended for custom intervals
scheduler = AsyncIOScheduler()

async def sync_service():
    async with async_get_db() as db:
        stmt = select(User).options(selectinload(User.notion_integration)).where(User.id == 7)
        result = await db.execute(stmt)
        users = result.scalars().all()
        for user in users:
            print(
                f"Hello from scheduler, {user.username}!"
            )
            notion = get_notion_client(user.notion_integration.access_token)
            notion_sync_result = await notion_sync_background(db=db, notion=notion, user_id=user.id)
            print(f"notion_sync_result: {notion_sync_result}")
# Function to start the scheduler
def start_scheduler():
    if not scheduler.running:
        scheduler.start()

scheduler.add_job(sync_service, 'interval', seconds=59, coalesce=False)

# Function to shutdown the scheduler
def shutdown_scheduler(wait=True):
    scheduler.shutdown(wait=wait)
