from app.common.rate_limit import rate_limit
from fastapi import APIRouter, Depends
from uuid import UUID
from app.core.store import require_investor, get_current_user
from app.core.dependency_chain import get_transaction_service
from app.business.transaction.schema.transaction_schema import (
    TransactionResponse,
    PaginatedTransactionResponse
)
from app.business.transaction.service.transaction_service import TransactionService
from app.common.pagination import PaginationParams
from app.platform.users.model.user import User

router = APIRouter(prefix="/investor/transactions", tags=["Investor Transactions"])




@router.get(
    "/user/{user_id}",
    response_model=PaginatedTransactionResponse,
    summary="Get paginated transactions by sender ID",
    dependencies=[
        Depends(rate_limit(limit=5, window=60))
    ],
    description="""
    Retrieves transactions initiated by a specific sender user ID.
    Supports high-performance Keyset Cursor pagination (primary) and Limit-Offset pagination (fallback).
    """
)
async def get_by_sender(
    user_id: UUID,
    params: PaginationParams = Depends(),
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user)
):
    return await service.get_sender_transactions_paginated(user_id, params)