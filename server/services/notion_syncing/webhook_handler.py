import datetime
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from dateutil import parser

from server.app.schemas.notion_pages import NotionTask
from server.db.models import UserNotionTask, User
from server.app.core.logging_config import logger
from server.db.models.enums import SyncStatus
from server.integrations.notion.notion_client import get_notion_client


class NotionWebhookService:
    def __init__(self):
        pass

    async def handle_page_deleted(self, db: AsyncSession, user_id: int, page_id: str):
        """
        Handles the deletion of a Notion page by updating the corresponding task in the database.

        This method processes the deletion of a Notion page by locating the corresponding
        task associated with the page and marking it as deleted in the database. If the task
        is not found, a warning is logged, and an error is returned. If the task is successfully
        marked as deleted, the updated task is committed and refreshed in the database.

        Parameters:
            db (AsyncSession): The asynchronous database session to interact with.
            user_id (int): The unique identifier of the user associated with the task.
            page_id (str): The unique identifier of the Notion page to be deleted.

        Returns:
            dict: A dictionary containing an error message if the task is not found;
                  otherwise, nothing is returned.

        Raises:
            Exception: Any exceptions raised during database operations are caught, and
            an error message is logged without interrupting the application flow.
        """
        try:
            stmt = select(UserNotionTask).where(
                UserNotionTask.user_id == user_id,
                UserNotionTask.notion_page_id == page_id
            )
            result = await db.execute(stmt)
            task = result.scalar_one_or_none()

            if not task:
                logger.warning(f"Task not found in database for page_id={page_id}")
                return {"error": "Task not found"}

            task.deleted = True
            task.deleted_at = datetime.now(datetime.timezone.utc)

            await db.commit()
            await db.refresh(task)
            logger.info(f"Task {task.id} marked as deleted.")
            return task
        except Exception as e:
            logger.error(f"Failed to handle page deleted: {e}")
            return {"error": str(e)}

    async def handle_page_created(self, db: AsyncSession, user: User, user_id: int, page_id: str):
        """
        Handles the event when a new page is created in Notion and integrates the information
        into the system's database as a new task while ensuring data integrity and handling
        various edge cases. The function retrieves the Notion page, processes it to create
        a task, and stores it in the database if it does not already exist.

        Arguments:
            db (AsyncSession): Asynchronous database session instance for database operations.
            user (User): User instance representing the current user.
            user_id (int): Unique identifier of the current user.
            page_id (str): Unique identifier of the Notion page.

        Raises:
            Exception: If an error occurs during the creation of a new task.

        Returns:
            dict: An error message if the task exists or if there are any issues while
            creating a new task. Otherwise, confirms the operation is successful.
        """
        notion_client = get_notion_client(user.notion_integration.access_token)
        page = await notion_client.pages.retrieve(page_id=page_id)
        notion_page = NotionTask.from_notion(page)
        logger.debug(f"Notion page: {notion_page.__dict__}")

        # Create
        stmt = select(UserNotionTask).where(
            UserNotionTask.user_id == user.id,
            UserNotionTask.notion_page_id == page_id
        )
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()

        # ! If task found
        if task:
            logger.warning(f"Task: {task.id} already exists in database")
            return {"error": "Task already exists"}

        # Create new task
        if not task:
            try:
                logger.debug(f"Creating new task for page_id: {page_id}")
                start_date = parser.isoparse(notion_page.start_date)
                end_date = parser.isoparse(notion_page.end_date)

                # if end_date < start_date:
                #     end_date = start_date
                #     logger.warning(f"End date is before start date for page_id: {page_id}")
                logger.debug(f"End date: {end_date}")
                if not end_date:
                    end_date = start_date + datetime.timedelta(hours=1)
                    logger.warning(f"End date is None, setting default end date for page_id: {task.id}")

                new_task_data = {
                    "user_id": user_id,
                    "notion_page_id": page_id,
                    "notion_url": notion_page.notion_page_url,
                    "title": notion_page.title,
                    "description": notion_page.description,
                    "status": notion_page.status,
                    "priority": notion_page.priority,
                    "select_option": notion_page.select_option,
                    "done": notion_page.done,
                    "start_date": start_date,
                    "end_date": end_date,
                    "sync_source": "notion",
                    "caldav_id": "pending",
                    "last_modified_source": "notion",
                    "sync_status": SyncStatus.pending,
                    "deleted": False,
                }

                # Note: NoneType error happened because all the columns cannot be NULL
                # TODO: Add user config to select automaticly end date range if not picked manually
                logger.debug(
                    f"Creating new task with data: {json.dumps(new_task_data, default=str, indent=4)}")
                new_task = UserNotionTask(
                    **new_task_data
                )
                db.add(new_task)
                await db.commit()
                await db.refresh(new_task)
            except Exception as e:
                logger.error(f"Error creating new task: {e}")
                return {"error": str(e)}

    async def handle_page_updated(self, db: AsyncSession, user: User, user_id: int, page_id: str):
        # Todo: get the page and update properties
        stmt = select(UserNotionTask).where(
            UserNotionTask.user_id == user.id,
            UserNotionTask.notion_page_id == page_id
        )
        result = await db.execute(stmt)
        task = result.scalar_one_or_none()

        if not task:
            logger.warning(f"Task not found in database for page_id={page_id}")
            return {"error": "Task not found"}
        else:
            try:
                notion_client = get_notion_client(user.notion_integration.access_token)
                page = await notion_client.pages.retrieve(page_id=page_id)
                notion_page = NotionTask.from_notion(page)
            except Exception as e:
                logger.error(f"Failed to get page: {e}")
                return None

            try:
                logger.debug(f"Task: {task.id} found in database")
                task.title = notion_page.title
                task.description = notion_page.description
                task.status = notion_page.status
                task.priority = notion_page.priority
                task.select_option = notion_page.select_option
                task.done = notion_page.done
                task.start_date = parser.isoparse(notion_page.start_date)
                task.end_date = parser.isoparse(notion_page.end_date)
                task.last_modified_source = "notion"
                task.sync_status = SyncStatus.pending

                await db.commit()
                await db.refresh(task)
                logger.info(f"Task {task.id} updated.")
            except Exception as e:
                logger.error(f"Error updating task: {e}")
                return {"error": str(e)}

