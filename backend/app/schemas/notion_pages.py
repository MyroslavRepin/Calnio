from typing import Optional
from pydantic import BaseModel


class NotionTask(BaseModel):
    id: str
    title: str
    notion_page_id: str
    notion_page_url: str
    task_date: Optional[str]
    status: Optional[str]
    done: bool
    priority: Optional[str]
    select_option: Optional[str]
    description: Optional[str]

    @classmethod
    def from_notion(cls, data: dict):
        props = data["properties"]

        # Title
        title = ""
        if props["Task"]["title"]:
            title = props["Task"]["title"][0]["plain_text"]

        # Description
        description = ""
        if props["Description"]["rich_text"]:
            description = props["Description"]["rich_text"][0]["plain_text"]

        # Task Date
        task_date = None
        if props["Task Date"]["date"]:
            task_date = props["Task Date"]["date"].get("start")

        # Status
        status = None
        if props["Status"]["status"]:
            status = props["Status"]["status"]["name"]

        # Done
        done = props["Done"]["checkbox"]

        # Priority
        priority = None
        if props["Priority"]["select"]:
            priority = props["Priority"]["select"]["name"]

        # Select Option
        select_option = None
        if props["Select"]["select"]:
            select_option = props["Select"]["select"]["name"]

        notion_page_id = data.get("id")
        notion_page_url = data.get(
            "url", f"https://www.notion.so/{notion_page_id}")

        #! Ignore this error
        return cls(
            id=data["id"],
            title=title,
            notion_page_id=notion_page_id,
            notion_page_url=notion_page_url,
            description=description,
            task_date=task_date,
            status=status,
            done=done,
            priority=priority,
            select_option=select_option,
        )
