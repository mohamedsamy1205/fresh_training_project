from uuid import UUID
from typing import Tuple, List, Union, Any
from sqlalchemy.orm import Session
from app.business.transaction.model.transaction import Transaction
from app.common.pagination import (
    PaginationParams,
    PaginationHelper,
    PagePaginationMeta
)


class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db


    def find_by_wallet_id(self, wallet_id: UUID) -> List[Transaction]:
        return self.db.query(Transaction).filter(Transaction.wallet_id == wallet_id).all()

    def get_by_sender_id_paginated(
        self,
        user_id: UUID,
        params: PaginationParams
    ) -> Tuple[List[Transaction], PagePaginationMeta]:
        """
        Retrieves paginated transactions for a specific sender user_id using page/limit.
        """
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)
        return PaginationHelper.paginate_query(
            query=query,
            model_class=Transaction,
            params=params,
            created_at_col=Transaction.created_at,
            id_col=Transaction.id
        )

    # Retained for backward compatibility
    def find_by_senderId(self, user_id: UUID) -> List[Transaction]:
        return self.db.query(Transaction).filter(Transaction.user_id == user_id).all()
