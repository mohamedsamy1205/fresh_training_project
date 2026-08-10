from uuid import UUID
from typing import Tuple, List, Union
from app.business.transaction.repository.transaction_repository import TransactionRepository
from app.business.transaction.schema.transaction_schema import (
    TransactionResponse,
    PaginatedTransactionResponse
)
from app.business.transaction.model.transaction import Transaction
from app.common.pagination import (
    PaginationParams,
    PaginatedResponse
)


class TransactionService:
    def __init__(self, repo: TransactionRepository):
        self.repo = repo


    async def get_sender_transactions_paginated(
        self,
        user_id: UUID,
        params: PaginationParams
    ) -> PaginatedTransactionResponse:
        """
        Business logic for retrieving sender transactions with pagination.
        Handles default bounds and calls the database repository layer.
        """
        items, meta = await self.repo.get_by_sender_id_paginated(user_id, params)
        # Convert ORM items to DTOs or pass items directly (handled by from_attributes=True)
        return PaginatedTransactionResponse(data=items, pagination=meta)


    # Legacy support
    def find_by_senderId(self, user_id: UUID) -> List[Transaction]:
        return self.repo.find_by_senderId(user_id)

    def find_by_walletId(self, wallet_id: UUID) -> List[Transaction]:
        return self.repo.find_by_wallet_id(wallet_id)