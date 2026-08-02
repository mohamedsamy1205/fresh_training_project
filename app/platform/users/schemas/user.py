from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from app.common.enums import UserRole

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: Optional[str] = None
    role: Optional[str] = "investor"
    provider: str
    age: Optional[int] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    role: Optional[UserRole] = None


class UserResponse(BaseModel):
    uuid: UUID
    name: str
    email: EmailStr
    age: Optional[int]
    role: UserRole

    class Config:
        from_attributes = True