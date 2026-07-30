from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: Optional[str] = None
    age: Optional[int] = None


class UserUpdate(BaseModel):
    name: Optional[str]
    age: Optional[int]


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    age: Optional[int]

    class Config:
        from_attributes = True