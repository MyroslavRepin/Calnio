from datetime import datetime
from pydantic import BaseModel

class CalDavEventModel(BaseModel):
    uid: str
    title: str
    start_date: datetime | None = None
    end_date: datetime | None = None
    status: str | None = None
    url: str | None = None