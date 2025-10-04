from server.db.deps import async_get_db_cm
from server.db.models import User
from server.integrations.notion.notion_client import get_notion_client
from server.utils.redis.utils import get_webhook_data
from server.db.redis_client import get_redis
from server.services.crud.tasks import sync_task_by_id

from sqlalchemy import select

async def sync_webhook_data():
    print(">>> Starting webhook sync")
    redis_client = await get_redis()
    webhook_data = await get_webhook_data(redis=redis_client, user_id=7)
    user_id = webhook_data["user_id"]
    page_id = webhook_data["page_id"]

    async with async_get_db_cm() as db:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()

        notion = get_notion_client(user.notion_integration.access_token)

        # Fixme:  Could not find page with ID. Make sure the relevant pages and databases are shared with your integration.
        await sync_task_by_id(db=db, notion=notion, user_id=user_id, page_id=page_id)
    print(">>> Webhook sync finished")
    return {"message": "Webhook data synced"}