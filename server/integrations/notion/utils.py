import pretty_errors
from typing import Optional
from pydantic import BaseModel
from server.app.core.config import settings


class NotionEvent(BaseModel):
    id: str
    title: str
    start_time: Optional[str]
    end_time: Optional[str]
    status: Optional[str]

    @classmethod
    def from_notion(cls, data: dict):
        props = data["properties"]

        # Title
        title = ""
        if props["Name"]["title"]:
            title = props["Name"]["title"][0]["text"]["content"]

        # Date
        start_time = None
        end_time = None
        if props["Date"]["date"]:
            start_time = props["Date"]["date"].get("start")
            end_time = props["Date"]["date"].get("end")

        # Status
        status = None
        if props["Status"]["select"]:
            status = props["Status"]["select"]["name"]

        return cls(
            id=data["id"],
            title=title,
            start_time=start_time,
            end_time=end_time,
            status=status
        )

# event = NotionEvent.from_notion(notion_page)
