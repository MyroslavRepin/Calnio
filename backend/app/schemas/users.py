from pydantic import BaseModel, EmailStr
from fastapi import Form
from pydantic import BaseModel, Field, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=30)
    hashed_password: str = Field(..., min_length=8)
    is_superuser: bool = False


# backend/app/schemas/users.py


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @classmethod
    def as_form(
        cls,
        email: str = Form(...),
        password: str = Form(...)
    ):
        return cls(email=email, password=password)
