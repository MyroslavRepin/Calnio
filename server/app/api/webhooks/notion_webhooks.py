from fastapi import APIRouter, Request
import json
from server.db.redis_client import get_redis
router = APIRouter()

@router.post("/webhooks/notion/")
async def get_notion_response(request: Request):
    redis_client = await get_redis()

    payload = await request.json()
    if not isinstance(payload, dict):
        return {"error": "Payload is not a dict"}

    print(">>> Notion webhook collected")
    page_id = payload["id"]
    if page_id:
        await redis_client.set("page_id", page_id)
        print(
            f">>> Set page_id in Redis: {page_id}"
        )

    return {"message": "Notion response", "response": payload}