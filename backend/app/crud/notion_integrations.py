from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.models.notion_integration import UserNotionIntegration


async def save_or_update_integration(db: AsyncSession, user_id: str, data: dict):
    result = await db.execute(
        select(UserNotionIntegration).where(
            UserNotionIntegration.user_id == user_id)
    )
    integration = result.scalars().first()

    if integration:
        # 🔄 Обновляем существующую интеграцию
        print("🔄 Updating existing integration")
        integration.access_token = data["access_token"]
        integration.workspace_id = data["workspace_id"]
        integration.workspace_name = data.get("workspace_name")
        integration.bot_id = data.get("bot_id")
        integration.notion_user_id = data["owner"]["user"]["id"]
        integration.duplicated_template_id = data.get("duplicated_template_id")
    else:
        # ➕ Создаём новую интеграцию
        print("➕ Adding new integration")
        integration = UserNotionIntegration(
            user_id=user_id,
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            workspace_id=data["workspace_id"],
            workspace_name=data.get("workspace_name"),
            bot_id=data.get("bot_id"),
            notion_user_id=data["owner"]["user"]["id"],
            duplicated_template_id=data.get("duplicated_template_id"),
        )
        db.add(integration)

    await db.commit()
    await db.refresh(integration)
    return integration
