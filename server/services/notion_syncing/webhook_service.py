from server.app.schemas.notion_pages import NotionTask
from server.db.deps import async_get_db_cm
from server.db.models import User
from server.integrations.notion.notion_client import get_notion_client
from server.utils.notion.utils import to_utc_datetime
from server.utils.redis.utils import get_webhook_data
from server.db.redis_client import get_redis
from server.services.crud.tasks import sync_task_by_id, create_task, delete_task

from sqlalchemy import select

async def sync_webhook_data():
    print(">>> ✅ Starting webhook sync")
    redis_client = await get_redis()
    webhook_data = await get_webhook_data(redis=redis_client, user_id=7)

    user_id = webhook_data["user_id"]
    page_id = webhook_data["page_id"]
    event_type = webhook_data["event_type"]
    async with async_get_db_cm() as db:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()

        notion_client = get_notion_client(user.notion_integration.access_token)

        page = await notion_client.pages.retrieve(page_id=page_id)
        notion_page = NotionTask.from_notion(page)
        start_date_utc = to_utc_datetime(notion_page.start_date)
        end_date_utc = to_utc_datetime(notion_page.end_date)


        # Function create_task works for updating too
        if event_type == "page.created":
            await create_task(
                db=db,
                user_id=user_id,
                title=notion_page.title,
                notion_page_id=page_id,
                notion_url=notion_page.notion_page_url,
                sync_source="notion",
                description=notion_page.description,
                # last_synced_at=notion_page.last_synced_at,
                caldav_uid="not supported yet",
                has_conflict=False,
                last_modified_source="notion",
                start_date=start_date_utc,
                end_date=end_date_utc,
                status=notion_page.status,
                done=notion_page.done,
                priority=notion_page.priority,
                select_option=notion_page.select_option,
            )

        elif event_type == "page.deleted":
            print(">>> Deleting task")
            await delete_task(db=db, user_id=user_id, page_id=page_id)



    print(">>> Webhook data: ", webhook_data)
    print(">>> ✅ Webhook sync finished")
    return {"message": "Webhook data synced"}