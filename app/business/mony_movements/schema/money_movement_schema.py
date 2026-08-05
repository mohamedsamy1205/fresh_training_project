from pydantic import BaseModel, Field
from uuid import UUID
from decimal import Decimal
from typing import Optional, List
from datetime import datetime
from app.common.enums import TransactionType, TransactionStatus, LedgerEntryType

class MoneyMovementRequest(BaseModel):
    user_id: UUID = Field(..., description="UUID of the user")
    amount: Decimal = Field(..., gt=Decimal("0.00"), description="Positive decimal amount")
    idempotency_key: str = Field(..., min_length=8, max_length=255, description="Unique key for request deduplication")
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
    amount: Decimal
    balance_after: Decimal
    created_at: datetime

    class Config:
        from_attributes = True

class TransactionResponse(BaseModel):
    uuid: UUID
    idempotency_key: str
    user_id: Optional[UUID]
    wallet_id: UUID
    amount: Decimal
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

    transaction_ids: List[UUID]

    amount: Decimal
    currency: str

    description: Optional[str] = None

    transactions: List[TransactionResponse]

    ledger_entries: List[LedgerEntryResponse]



