from fastapi import APIRouter, HTTPException, Request, Depends, Response
from fastapi.responses import RedirectResponse
import httpx

from backend.app.db.deps import async_get_db
from backend.app.db.database import AsyncSession
from backend.app.services.notion_integrations import save_or_update_integration
from backend.app.security.utils import access_token_required, refresh_access_token
from backend.app.core.config import settings

import logging

router = APIRouter()


@router.get("/oauth/callback")
async def oauth_callback(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(async_get_db),
):
    print(f"Request: {request.cookies}")
    # ! Checking for tokens & updating them
    try:
        # 🛡️ Проверка токена
        payload = await access_token_required(request)
        user_id = int(payload["sub"])
    except HTTPException:
        try:
            # ♻️ Обновление access токена
            logging.info("🔁 Trying to refresh access token")
            payload = await refresh_access_token(request, response)
            user_id = int(payload["sub"])
        except HTTPException:
            logging.warning("❌ Unauthorized — redirect to /login")
            return RedirectResponse("/login", status_code=401)
    # Getting error message from the query

    code = request.query_params.get("code")

    if not code:
        logging.error("⚠️ OAuth code not found in callback URL")
        raise HTTPException(
            status_code=400, detail="Code not found in query params")

    token_url = "https://api.notion.com/v1/oauth/token"

    notion_redirect_uri = settings.notion_redirect_uri

    print(f"Notion redirect uri: {notion_redirect_uri}")

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": notion_redirect_uri
    }

    # Taking data from settings (ORM)

    OAuth_Client_ID = settings.notion_client_id
    OAuth_Client_Secret = settings.notion_secert

    if not OAuth_Client_ID or not OAuth_Client_Secret:
        logging.critical("❗Missing OAuth client credentials")
        raise HTTPException(
            status_code=500, detail="OAuth credentials not set in environment")

    auth = (OAuth_Client_ID, OAuth_Client_Secret)

    headers = {
        "Content-Type": "application/json"
    }
    print("Sending to Notion:", data)
    async with httpx.AsyncClient() as client:
        response_data = await client.post(token_url, json=data, auth=auth, headers=headers)

    print("POST data sent to Notion:", data)
    print("Notion response status:", response_data.status_code)
    print("Notion response body:", response_data.text)

    if response_data.status_code != 200:
        logging.error(
            f"🚫 Notion token request failed: {response_data.status_code}")
        logging.error(f"📝 Response body: {response_data.text}")
        print("Notion response:", response_data.status_code, response_data.text)
        raise HTTPException(
            status_code=500, detail="Failed to exchange token with Notion")

    token_data = response_data.json()

    logging.info("🔐 Notion OAuth Token Response:")
    logging.info(token_data)

    await save_or_update_integration(db, user_id, token_data)
    # Optimize: If user canceled integration -> redirect
    error = request.query_params.get("error")
    if error == "access_denied":
        # пользователь отменил авторизацию
        logging.critical("User canceled integration")
        return RedirectResponse(url="/dashboard")

    return RedirectResponse("/dashboard?success=1", status_code=302)
