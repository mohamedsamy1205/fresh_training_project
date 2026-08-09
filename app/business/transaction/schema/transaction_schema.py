from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from uuid import UUID
from typing import Optional
from datetime import datetime
from app.common.enums import TransactionType, TransactionStatus
from app.common.utils.money import MoneyAmount
from app.common.pagination import PaginatedResponse



class TransactionUpdate(BaseModel):
    status: Optional[TransactionStatus] = None
    description: Optional[str] = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    user_id: Optional[UUID] = None
    wallet_id: UUID
    amount: MoneyAmount
    currency: str = "USD"
    type: TransactionType
    status: TransactionStatus
    description: Optional[str] = None
    created_at: datetime


PaginatedTransactionResponse = PaginatedResponse[TransactionResponse]