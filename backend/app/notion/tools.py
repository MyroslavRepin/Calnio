from pydantic import BaseModel
from typing import Optional
import pretty_errors


class NotionEvent(BaseModel):
    id: str
    title: str
    start_time: Optional[str]
    end_time: Optional[str]
    # status: Optional[str]

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


# воображаемый JSON от Notion
notion_page = {
    "id": "e1c12345-6789-4abc-def0-1234567890ab",
    "properties": {
        "Name": {
            "title": [
                {"type": "text", "text": {"content": "Meeting with John"}}
            ]
        },
        "Date": {
            "date": {"start": "2025-09-07T14:00:00.000+00:00", "end": "2025-09-07T15:00:00.000+00:00"}
        },
        "Status": {
            "select": {"id": "123", "name": "In Progress", "color": "blue"}
        }
    }
}

event = NotionEvent.from_notion(notion_page)
print(event.title)       # Meeting with John
print(event.start_time)  # 2025-09-07T14:00:00.000+00:00
print(event.status)      # In Progress
