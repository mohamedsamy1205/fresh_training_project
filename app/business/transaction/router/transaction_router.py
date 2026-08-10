from fastapi import APIRouter, Depends
from uuid import UUID
from app.core.security import require_investor, get_current_user
from app.core.dependency_chain import get_transaction_controller
from app.business.transaction.schema.transaction_schema import (
    TransactionResponse,
    PaginatedTransactionResponse
)
from app.business.transaction.controller.transaction_controller import TransactionController
from app.common.pagination import PaginationParams
from app.platform.users.model.user import User

router = APIRouter(prefix="/investor/transactions", tags=["Investor Transactions"])




@router.get(
    "/user/{user_id}",
    response_model=PaginatedTransactionResponse,
    summary="Get paginated transactions by sender ID",
    description="""
    Retrieves transactions initiated by a specific sender user ID.
    Supports high-performance Keyset Cursor pagination (primary) and Limit-Offset pagination (fallback).
    """
)
def get_by_sender(
    user_id: UUID,
    params: PaginationParams = Depends(),
    controller: TransactionController = Depends(get_transaction_controller),
    current_user: User = Depends(get_current_user)
):
    return controller.get_sender_transactions(user_id, params)