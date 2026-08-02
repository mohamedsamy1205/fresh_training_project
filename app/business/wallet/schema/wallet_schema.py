from pydantic import BaseModel, Field
from decimal import Decimal
from uuid import UUID


class WalletCreate(BaseModel):
    user_id: UUID
    name: str

class WalletUpdate(BaseModel):
    Wallet_id: UUID
    new_balance: Decimal

class WalletResponse(BaseModel):
    Wallet_id: UUID = Field(alias="uuid")
    balance: Decimal
    wallet_name: str = Field(alias="name")

    class Config:
        from_attributes = True
