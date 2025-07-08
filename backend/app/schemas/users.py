from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    username: str
    password: str
