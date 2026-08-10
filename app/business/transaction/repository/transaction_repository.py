from uuid import UUID
from typing import Tuple, List, Union, Any
from app.business.mony_movements.schema.money_movement_schema import TransactionResponse
from sqlalchemy.orm import Session
import json
from app.business.transaction.model.transaction import Transaction
from app.common.pagination import (
    PaginationParams,
    PaginationHelper,
    PagePaginationMeta
)


class TransactionRepository:
    def __init__(self, db: Session, redis):
        self.db = db
        self.redis = redis


    def find_by_wallet_id(self, wallet_id: UUID) -> List[Transaction]:
        return self.db.query(Transaction).filter(Transaction.wallet_id == wallet_id).all()

    async def get_by_sender_id_paginated(
        self,
        user_id: UUID,
        params: PaginationParams
    ) -> Tuple[List[Transaction], PagePaginationMeta]:

        cache_key = f"user:{user_id}:page:{params.page}:limit:{params.limit}"

        # 1️⃣ Try Redis
        cached_transction = await self.redis.get(cache_key)
        if cached_transction:
            cached_transction = json.loads(cached_transction)
            items = cached_transction["items"]
            if items:
                meta = PagePaginationMeta(**cached_transction["meta"])
                return items, meta

        # 2️⃣ Get from DB
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)
        print(query.count())
        items, meta = PaginationHelper.paginate_query(
            query=query,
            model_class=Transaction,
            params=params,
            created_at_col=Transaction.created_at,
            id_col=Transaction.id
        )

        data = {
        "items": [
            TransactionResponse.model_validate(item).model_dump(mode="json")
            for item in items
        ],
        "meta": meta.dict()
    }

        await self.redis.setex(cache_key, 600, json.dumps(data))

        # 4️⃣ Return الصحيح
        return items, meta

    # Retained for backward compatibility
    def find_by_senderId(self, user_id: UUID) -> List[Transaction]:
        return self.db.query(Transaction).filter(Transaction.user_id == user_id).all()
