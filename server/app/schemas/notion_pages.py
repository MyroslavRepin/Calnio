import json
from typing import Optional, Dict, Any
from pydantic import BaseModel
from pygments.styles.gh_dark import FG_SUBTLE

from server.utils.notion.utils import to_notion_time


class NotionTask(BaseModel):
    id: str
    title: str
    notion_page_id: str
    notion_page_url: str
    start_date: Optional[str]
    end_date: Optional[str]  # New field
    status: Optional[str]
    done: bool
    priority: Optional[str]
    select_option: Optional[str]
    description: Optional[str]
    # Updated default values for new columns
    sync_source: Optional[str] = "notion"
    last_synced_at: Optional[str] = None
    caldav_uid: Optional[str] = None
    has_conflict: Optional[bool] = False
    last_modified_source: Optional[str] = "notion"

    @classmethod
    def from_notion(cls, data: dict):
        """
        Transform Notion data JSON into a NotionTask (ORM) instance.

        Args:
            data (dict): The JSON object representing a Notion page, typically as returned by the Notion API.

        Returns:
            NotionTask: An instance of NotionTask populated with data extracted from the Notion page.

        This method extracts and maps the following fields:
            - title: The main task title from the 'Task' property.
            - description: The task description from the 'Description' property.
            - start_date, end_date: The start and end dates from the 'Task Date' property.
            - status: The current status from the 'Status' property.
            - done: Boolean indicating if the task is completed, from the 'Done' property.
            - priority: The priority level from the 'Priority' property.
            - select_option: Additional select option from the 'Select' property.
            - notion_page_id: The unique Notion page ID.
            - notion_page_url: The URL to the Notion page.
            - sync_source, last_synced_at, caldav_uid, has_conflict, last_modified_source:
            Additional metadata, using defaults if not present in the input data.

        Raises:
            KeyError: If required properties are missing from the input data.
        """
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
        start_date = None
        end_date = None
        if props["Task Date"]["date"]:
            start_date = props["Task Date"]["date"].get("start")
            end_date = props["Task Date"]["date"].get("end")

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

        # Use default values for new columns unless provided in data
        sync_source = data.get("sync_source", "notion")
        last_synced_at = data.get("last_synced_at", None)
        caldav_uid = data.get("caldav_uid", None)
        has_conflict = data.get("has_conflict", False)
        last_modified_source = data.get("last_modified_source", "notion")

        return cls(
            id=data["id"],
            title=title,
            notion_page_id=notion_page_id,
            notion_page_url=notion_page_url,
            description=description,
            start_date=start_date,
            end_date=end_date,
            status=status,
            done=done,
            priority=priority,
            select_option=select_option,
            sync_source=sync_source,
            last_synced_at=last_synced_at,
            caldav_uid=caldav_uid,
            has_conflict=has_conflict,
            last_modified_source=last_modified_source,
        )

    @classmethod
    def to_notion(cls, task: "NotionTask"):
        """Transform NotionTask (ORM) instance into a Notion data JSON.
        Args:
            - task (NotionTask): An instance of NotionTask to be converted into Notion API format.
        Returns:
            - dict: A dictionary formatted for the Notion API to create or update a page.
        This method constructs a Notion-compatible JSON object with the following properties:
        """
        # Todo: Check if some data from db is None -> To not update json

        # Todo: Get changes in db from Redis and update json
        if not task.sync_source == "notion":
            notion_data: Dict[str, Any] = {
                "properties": {
                    "Task Date": {
                        "date": {
                            "start": to_notion_time(task.start_date),
                            "end": to_notion_time(task.end_date),
                        }
                    },
                    "Priority": {
                        "select": {
                            "name": task.priority,
                        }
                    },
                    "Description": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": task.description
                                }
                            }
                        ]
                    },
                    "Status": {
                        "status": {
                            "name": task.status,
                        }
                    },
                    "Select": {
                        "select": {
                            "name": task.select_option,
                        }
                    },
                    "Done": {
                        "checkbox": task.done
                    },
                }
            }
            return notion_data