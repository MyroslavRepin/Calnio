from fastapi import APIRouter, Request
import json
router = APIRouter()

@router.post("/webhooks/notion/")
async def get_notion_response(request: Request):
    # notion_response = request.query_params.get()
    payload = await request.json()
    pretty_json = json.dumps(payload, indent=4)
    print(pretty_json)
    return {"message": "Notion response", "response": request.query_params}
