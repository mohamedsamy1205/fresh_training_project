from pydantic import BaseModel
from decimal import Decimal
from uuid import UUID
from typing import Optional
from app.common.enums import TransactionType, TransactionStatus
from datetime import datetime

class TransactionCreate(BaseModel):
    wallet_id: UUID
    amount: Decimal
    type: TransactionType
    status: TransactionStatus = TransactionStatus.PENDING.value
    sender_id: Optional[UUID] = None
    description: Optional[str] = None


class TransactionUpdate(BaseModel):
    status: Optional[TransactionStatus] = None
    description: Optional[str] = None


class TransactionResponse(BaseModel):
    uuid: UUID
    sender_id: UUID
    wallet_id: UUID
    amount: float
    type: TransactionType
    status: TransactionStatus
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True  