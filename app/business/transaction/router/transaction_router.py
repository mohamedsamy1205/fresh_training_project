from fastapi import APIRouter, Depends
from uuid import UUID
from app.core.security import require_investor
from app.core.dependency_chain import get_transaction_service
from app.business.transaction.schema.transaction_schema import (
    TransactionCreate,
    TransactionResponse
)
from app.business.transaction.service.transaction_service import TransactionService
from app.platform.users.model.user import User

router = APIRouter(prefix="/investor/transactions", tags=["Investor Transactions"])


@router.post(
    "",
    response_model=TransactionResponse,
    summary="Create transaction",
    description="""
    Investor endpoint.

    Creates a new financial transaction between investor wallets.
    """
)
def create_transaction(
    data: TransactionCreate,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(require_investor)
):
    return service.create(data)


@router.get(
    "/sender/{user_id}",
    response_model=list[TransactionResponse],
    summary="Get transactions by sender ID",
    description="""
    Investor endpoint.

    Retrieves all transactions initiated by a specific sender user ID.
    """
)
def get_by_sender(
    user_id: UUID,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(require_investor)
):
    return service.find_by_senderId(user_id)


@router.get(
    "/wallet/{wallet_id}",
    response_model=list[TransactionResponse],
    summary="Get transactions by wallet ID",
    description="""
    Investor endpoint.

    Retrieves transaction history for a specified wallet ID.
    """
)
def get_by_wallet(
    wallet_id: UUID,
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(require_investor)
):
    return service.find_by_walletId(wallet_id)