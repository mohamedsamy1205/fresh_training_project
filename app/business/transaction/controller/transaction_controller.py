from uuid import UUID
from app.business.transaction.service.transaction_service import TransactionService
from app.business.transaction.schema.transaction_schema import (
    TransactionResponse,
    PaginatedTransactionResponse
)
from app.common.pagination import PaginationParams
from app.business.transaction.model.transaction import Transaction


class TransactionController:
    def __init__(self, service: TransactionService):
        self.service = service


    def get_sender_transactions(
        self,
        user_id: UUID,
        params: PaginationParams
    ) -> PaginatedTransactionResponse:
        """
        Orchestrates fetching paginated transactions for a sender user.
        """
        return self.service.get_sender_transactions_paginated(user_id, params)

