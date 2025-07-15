from pydantic import BaseModel, Field, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8)
    is_superuser: bool = False
