# from server.db.deps import async_get_db_cm
# from server.db.models.users import User
# from server.db.models.tasks import UserNotionTask
# from server.db.models.calendars import Calendar
# from sqlalchemy import select
# from server.app.core.logging_config import logger
# from server.services.caldav.caldav_orm import CalDavORM
# from server.utils.utils import extract_uid
#
# async def sync_user_events():
#     # TODO: Implement for loop to sync all filtered users
#     user_id = 7
#     orm = CalDavORM(user_id=user_id)
#     await orm.authenticate()
#     calendar = await orm.Calendar.get_by_name("Personal")
#
#     async with async_get_db_cm() as db:
#         stmt = (
#             select(UserNotionTask)
#             .where(
#                 UserNotionTask.user_id == user_id,
#                 UserNotionTask.start_date.is_not(None),
#                 UserNotionTask.end_date.is_not(None)
#             )
#         )
#         result = await db.execute(stmt)
#         tasks = result.scalars().all()
#
#         for task in tasks:
#             logger.info(f"Syncing task '{task.title}' for user ID: {user_id}")
#
#             try:
#
#                 await orm.Event.create(
#                     calendar_uid=extract_uid(calendar.id),
#                     title=task.title,
#                     description=task.description,
#                     location=None,
#                     start=task.start_date,
#                     end=task.end_date,
#                 )
#                 logger.info(f"Successfully synced task '{task.title}'")
#             except Exception as e:
#                 logger.error(f"Failed to sync task '{task.title}': {e}")