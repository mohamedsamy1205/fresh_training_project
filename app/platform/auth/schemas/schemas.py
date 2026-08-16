from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SessionResponse(BaseModel):
    uuid: UUID
    device_name: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    last_seen: datetime
    expires_at: datetime
    revoked: bool
    revoked_at: Optional[datetime] = None
    is_current: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str