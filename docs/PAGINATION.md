# Pagination Architecture & Reusability Guide

This document details the standardized pagination system implemented across the application (`app/common/pagination.py`). It explains the architecture of the Page/Limit pagination utility, response schema envelopes, repository helpers, and database index optimizations.

---

## 1. Core Architecture & Layers

Pagination follows Clean Architecture across all layers:

```
┌──────────────────────────────────────────────────────────┐
│                      1. Router                           │
│   Binds query params via PaginationParams:               │
│   - page (default: 1, min: 1)                            │
│   - limit (default: 20, min: 1, max: 100)                │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│                     2. Service                           │
│   Calls repository and returns PaginatedResponse[DTO].   │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│                    3. Repository                         │
│   Constructs base SQLAlchemy Query and passes to         │
│   PaginationHelper.paginate_query().                     │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│               4. PaginationHelper                        │
│   Executes COUNT(*), applies OFFSET and LIMIT, orders by │
│   (created_at DESC, id DESC), and computes metadata.     │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Reusable Pagination Utility (`app/common/pagination.py`)

### 2.1. Classes & Responsibilities

| Class / Component | Type | Responsibility |
| :--- | :--- | :--- |
| `PaginationParams` | Pydantic Model / FastAPI Dependency | Binds and validates query parameters (`page: int = 1`, `limit: int = 20`, max `100`). |
| `PagePaginationMeta` | Pydantic Model | Metadata schema returning `page`, `limit`, `total`, `total_pages`, `has_next`, and `has_prev`. |
| `PaginatedResponse[T]` | Generic Pydantic Model | Standardized response envelope containing `data: List[T]` and `pagination: PagePaginationMeta`. |
| `PaginationHelper` | Static Helper Class | Applies SQL offset, limit, count calculation, and deterministic descending sorting (`created_at DESC, id DESC`). |

### 2.2. Schema Definitions

```python
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number (1-based index)")
    limit: int = Field(20, ge=1, le=100, description="Items per page")


class PagePaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)

    data: List[T]
    pagination: PagePaginationMeta
```

---

## 3. Standard JSON Response Format

Paginated endpoints (e.g. `GET /investor/transactions/user/{user_id}?page=1&limit=20`) return data structured as follows:

```json
{
  "data": [
    {
      "uuid": "c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f",
      "user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
      "wallet_id": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
      "amount": "250.00",
      "currency": "USD",
      "type": "deposit",
      "status": "success",
      "description": "Initial funding",
      "created_at": "2026-08-19T08:15:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 125,
    "total_pages": 7,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## 4. How to Plug Pagination into New Entities

To add pagination to any entity (e.g. `Wallet`, `Investment`, `Project`), follow these steps:

### Step 1: Ensure Composite Index on Model
Ensure your SQLAlchemy model has an index covering filter foreign keys and sorting columns (`created_at`, `id`):

```python
from sqlalchemy import Index

class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("idx_transactions_user_created_id", "user_id", "created_at", "id"),
    )
```

### Step 2: Use `PaginationHelper.paginate_query()` in Repository

```python
from app.common.pagination import PaginationParams, PaginationHelper
from app.business.transaction.model.transaction import Transaction

class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    async def get_by_sender_id_paginated(self, user_id: UUID, params: PaginationParams):
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)
        return PaginationHelper.paginate_query(
            query=query,
            model_class=Transaction,
            params=params,
            created_at_col=Transaction.created_at,
            id_col=Transaction.id
        )
```

### Step 3: Implement Service Layer Method

```python
class TransactionService:
    def __init__(self, repo: TransactionRepository):
        self.repo = repo

    async def get_sender_transactions_paginated(
        self,
        user_id: UUID,
        params: PaginationParams
    ) -> PaginatedTransactionResponse:
        items, meta = await self.repo.get_by_sender_id_paginated(user_id, params)
        return PaginatedTransactionResponse(data=items, pagination=meta)
```

### Step 4: Expose in Router

```python
@router.get(
    "/user/{user_id}",
    response_model=PaginatedTransactionResponse,
    summary="Get paginated transactions by sender ID"
)
async def get_by_sender(
    user_id: UUID,
    params: PaginationParams = Depends(),
    service: TransactionService = Depends(get_transaction_service),
    current_user: User = Depends(get_current_user)
):
    return await service.get_sender_transactions_paginated(user_id, params)
```
