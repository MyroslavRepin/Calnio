from server.db.models import users as user_models
from server.db.models import waitlist as waitlist_models
from server.db.models import notion_integration as notion_integration_models
from sqladmin import Admin
from sqladmin import ModelView

class UserAdmin(ModelView, model=user_models.User):
    column_list = [
        user_models.User.id,
        user_models.User.email,
        user_models.User.username,
        user_models.User.is_superuser
    ]

class WaitlistAdmin(ModelView, model=waitlist_models.Waitlist):
    column_list = [
        waitlist_models.Waitlist.id,
        waitlist_models.Waitlist.email,
        waitlist_models.Waitlist.created_at,
        waitlist_models.Waitlist.discount,
    ]

class NotionIntegrationAdmin(ModelView, model=notion_integration_models.UserNotionIntegration):
    column_list = [
        notion_integration_models.UserNotionIntegration.id,
        notion_integration_models.UserNotionIntegration.user_id,
        notion_integration_models.UserNotionIntegration.access_token,
        notion_integration_models.UserNotionIntegration.refresh_token,
        notion_integration_models.UserNotionIntegration.workspace_id,
    ]

