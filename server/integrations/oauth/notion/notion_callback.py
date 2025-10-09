from fastapi import APIRouter, HTTPException, Request, Depends, Response
from fastapi.responses import RedirectResponse
import httpx

from server.db.deps import async_get_db
from server.db.database import AsyncSession
from server.services.notion_syncing.notion_integrations import save_or_update_integration
from server.utils.security.utils import access_token_required, refresh_access_token
from server.app.core.config import settings
from server.app.core.logging_config import logger

router = APIRouter()


@router.get("/oauth/callback")
async def oauth_callback(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(async_get_db),
):
    logger.debug(f"OAuth callback request with cookies: {request.cookies}")
    # ! Checking for tokens & updating them
    try:
        # 🛡️ Проверка токена
        payload = await access_token_required(request)
        user_id = int(payload["sub"])
    except HTTPException:
        try:
            logger.info("Trying to refresh access token")
            payload = await refresh_access_token(request, response)
            user_id = int(payload["sub"])
        except HTTPException:
            logger.warning("Unauthorized — redirect to /login")
            return RedirectResponse("/login", status_code=401)
    # Getting error message from the query

    code = request.query_params.get("code")

    if not code:
        logger.error("OAuth code not found in callback URL")
        raise HTTPException(
            status_code=400, detail="Code not found in query params")

    token_url = "https://api.notion.com/v1/oauth/token"

    notion_redirect_uri = settings.notion_redirect_uri

    logger.debug(f"Notion redirect URI: {notion_redirect_uri}")

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": notion_redirect_uri
    }

    # Taking data from settings (ORM)

    OAuth_Client_ID = settings.notion_client_id
    OAuth_Client_Secret = settings.notion_secert

    if not OAuth_Client_ID or not OAuth_Client_Secret:
        logger.critical("Missing OAuth client credentials")
        raise HTTPException(
            status_code=500, detail="OAuth credentials not set in environment")

    auth = (OAuth_Client_ID, OAuth_Client_Secret)

    headers = {
        "Content-Type": "application/json"
    }
    logger.debug(f"Sending OAuth request to Notion")
    async with httpx.AsyncClient() as client:
        response_data = await client.post(token_url, json=data, auth=auth, headers=headers)

    logger.debug(f"Notion response status: {response_data.status_code}")

    if response_data.status_code != 200:
        logger.error(f"Notion token request failed: {response_data.status_code}")
        logger.error(f"Response body: {response_data.text}")
        raise HTTPException(
            status_code=500, detail="Failed to exchange token with Notion")

    token_data = response_data.json()

    logger.info("Notion OAuth token received successfully")
    logger.debug(f"Token data: {token_data}")

    await save_or_update_integration(db, user_id, token_data)
    # Optimize: If user canceled integrations -> redirect
    error = request.query_params.get("error")
    if error == "access_denied":
        # User canceled Notion OAuth, redirect to dashboard
        logger.warning("User canceled OAuth integration")
        return RedirectResponse(url="/dashboard", status_code=302)

    logger.info("Notion integration saved successfully")
    return RedirectResponse("/dashboard?success=1", status_code=302)
