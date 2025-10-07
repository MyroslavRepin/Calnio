import logging

from datetime import datetime, timezone
from dateutil import parser

from notion_client import AsyncClient


def normalize_notion_id(notion_id: str) -> str:
    """
    Normalize a Notion ID by removing all dashes.
    Example: '284a5558-72b4-8086-82c3-da846290d940' -> '284a555872b4808682c3da846290d940'
    """
    if not notion_id:
        return notion_id
    return notion_id.replace("-", "")


async def get_all_ids(notion: AsyncClient):
    result = await notion.search()
    database_ids = [
        obj["id"]
        for obj in result["results"]
        if obj["object"] == "database"
    ]

    page_ids = []
    for db_id in database_ids:
        query_result = await notion.databases.query(database_id=db_id)
        for row in query_result.get("results", []):
            if row["object"] == "page":
                page_id = row["id"]
                try:
                    page_test = await notion.pages.retrieve(page_id=page_id)
                    if page_test.get("url"):
                        # Return page_id with dashes (Notion API format)
                        # Normalization will happen in the calling functions
                        page_ids.append(page_id)
                except Exception as e:
                    # Note: This still uses logging.warning for backward compatibility
                    # If you need Loguru here, import logger from logging_config
                    logging.warning(
                        f"Page {page_id} could not be retrieved: {e}")

    return page_ids

def to_notion_time(db_time):
    notion_time = db_time.isoformat()
    return notion_time

def to_utc_datetime(dt):
    """
    Convert a date string or datetime object to a UTC-aware datetime (timestamptz compatible).
    Accepts ISO 8601 strings or datetime objects (naive or aware).
    Returns a timezone-aware datetime in UTC.
    """
    if dt is None:
        return None

    # Parse string to datetime
    if isinstance(dt, str):
        try:
            parsed = parser.isoparse(dt)
        except Exception:
            return None
    elif isinstance(dt, datetime):
        parsed = dt
    else:
        return None

    # If naive, assume UTC
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)

    # Convert aware datetime to UTC
    return parsed.astimezone(timezone.utc)