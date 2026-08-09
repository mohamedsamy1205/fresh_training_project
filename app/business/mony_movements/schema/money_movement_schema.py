from pydantic import BaseModel, Field
from uuid import UUID
from decimal import Decimal
from typing import Optional, List
from datetime import datetime
from app.common.enums import TransactionType, TransactionStatus, LedgerEntryType
from app.common.utils.money import MoneyAmount

import uuid

class MoneyMovementRequest(BaseModel):
    user_id: UUID = Field(..., description="UUID of the user")
    amount: MoneyAmount = Field(..., gt=Decimal("0.00"), description="Positive decimal amount")
    idempotency_key: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique key for request deduplication")
    description: Optional[str] = Field(None, max_length=500)

class DepositRequest(MoneyMovementRequest):
    pass

class WithdrawRequest(MoneyMovementRequest):
    pass

class LedgerEntryResponse(BaseModel):
    uuid: UUID
    transaction_id: UUID
    wallet_id: UUID
    entry_type: str
    amount: MoneyAmount
    balance_after: MoneyAmount
    created_at: datetime

    class Config:
        from_attributes = True

class TransactionResponse(BaseModel):
    uuid: UUID
    idempotency_key: str
    user_id: Optional[UUID]
    wallet_id: UUID
    amount: MoneyAmount
    currency: str
    type: TransactionType
    status: TransactionStatus
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class MoneyMovementResponse(BaseModel):
    success: bool
    duplicate: bool = False

    transaction: TransactionResponse
    ledger_entries: List[LedgerEntryResponse]
