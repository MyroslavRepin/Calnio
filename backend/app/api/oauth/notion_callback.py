import uuid
from datetime import datetime

from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
import httpx
import os

from backend.app.db.deps import async_get_db
from backend.app.db.database import AsyncSession
from backend.app.models.notion_integration import UserNotionIntegration
from backend.app.crud.notion_integrations import save_or_update_integration
router = APIRouter()


@router.get("/oauth/callback")
async def oauth_callback(request: Request, db: AsyncSession = Depends(async_get_db)):
    code = request.query_params.get("code")

    if not code:
        return {"error": "Code not found in query params"}

    token_url = "https://api.notion.com/v1/oauth/token"

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://localhost:8000/oauth/callback"
    }

    OAuth_Client_ID = os.getenv("OAuth_Client_ID")
    OAuth_Client_Secret = os.getenv("OAuth_Client_Secret")

    auth = (OAuth_Client_ID, OAuth_Client_Secret)

    headers = {
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, json=data, auth=auth, headers=headers)

    token_data = response.json()

    print("🔐 Notion Response:")
    print(token_data)

    # TODO: Получить user_id из текущей сессии / авторизации
    id = 1
    integration_data = response.json()
    await save_or_update_integration(db, id, integration_data)

    return RedirectResponse("/dashboard?success=1", 302)
