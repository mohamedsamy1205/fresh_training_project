from fastapi import APIRouter, Depends
from uuid import UUID
from app.core.security import get_current_user
from app.core.dependency_chain import get_transaction_service
from app.business.transaction.schema.transaction_schema import (
    TransactionCreate,
    TransactionResponse
)
from app.business.transaction.service.transaction_service import TransactionService
from app.platform.users.model.user import User

router = APIRouter(prefix="/transactions", tags=["Transactions"])


# ========================
# Create Transaction
# ========================
@router.post("/", response_model=TransactionResponse)
def create_transaction(
    data: TransactionCreate,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user)
):
    return service.create(data)


# ========================
# Get by Sender ID
# ========================
@router.get("/sender/{user_id}", response_model=list[TransactionResponse])
def get_by_sender(
    user_id: UUID,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user)
):
    return service.find_by_senderId(user_id)


# ========================
# Get by Wallet ID
# ========================
@router.get("/wallet/{wallet_id}", response_model=list[TransactionResponse])
def get_by_wallet(
    wallet_id: UUID,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user)
):
    return service.find_by_walletId(wallet_id)