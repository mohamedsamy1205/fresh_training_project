# Production Pagination Architecture & Reusability Guide

This document provides a comprehensive reference for the production-grade pagination system implemented across the application. It details how the **Keyset (Cursor-Based) Pagination** and **Limit-Offset Fallback** operate, how to reuse the system for new endpoints (e.g., Wallets, Investments, Projects), and the underlying SQLAlchemy B-Tree index optimizations.

---

## 1. Core Architecture & Layers

The implementation strictly enforces Clean Architecture across 4 core layers:

```
┌──────────────────────────────────────────────────────────┐
│                      1. Router                           │
│   Receives HTTP requests & binds query params:           │
│   - cursor & limit (Keyset mode)                         │
│   - page & size (Offset mode)                            │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│                     2. Controller                        │
│   Orchestrates request flow between FastAPI dependency   │
│   injections and application services.                   │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│                     3. Service                           │
│   Applies domain constraints, business security rules,   │
│   and default boundary limits.                           │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│                    4. Repository                         │
│   Constructs base SQLAlchemy query and delegates to      │
│   PaginationHelper for index-backed pagination.          │
└────────────────────────────┬─────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────┐
│               5. PaginationHelper                        │
│   Encodes opaque base64 cursors, applies tuple comparison│
│   WHERE (created_at, id) < (cursor_time, cursor_id),     │
│   and returns standardized PaginatedResponse schemas.    │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Reusable Pagination Utility (`app/common/pagination.py`)

### 2.1. Classes & Responsibilities

| Class / Component | Type | Responsibility |
| :--- | :--- | :--- |
| `PaginationParams` | Pydantic Model / FastAPI Dependency | Accepts query parameters (`cursor`, `limit`, `page`, `size`), validates constraints (`limit` $\le 100$), and auto-detects cursor vs offset mode. |
| `CursorEncoder` | Base64 Utility | Encodes compound tuple keys `(created_at, id)` into opaque, URL-safe Base64 strings and decodes them back to native Python types. |
| `CursorPaginationMeta` | Pydantic Model | Metadata schema for Keyset mode: returns `next_cursor`, `limit`, and `has_next`. |
| `OffsetPaginationMeta` | Pydantic Model | Metadata schema for Offset mode: returns `page`, `size`, `total`, and `total_pages`. |
| `PaginatedResponse[T]` | Generic Pydantic Model | Standardized response envelope containing `data: List[T]` and `pagination: Union[CursorPaginationMeta, OffsetPaginationMeta]`. |
| `PaginationHelper` | Static Helper Class | Applies keyset SQL filters, deterministic sorting (`created_at DESC, id DESC`), peek fetching (`limit + 1`), or count-offset queries. |

---

## 3. How to Plug Pagination into New Endpoints

To add pagination to any entity (e.g. `Wallet`, `Investment`, `Project`), follow these 3 steps:

### Step 1: Add a Composite B-Tree Index to your SQLAlchemy Model

Ensure your model has a compound index covering the filtering foreign key, `created_at`, and `id`:

```python
from sqlalchemy import Index

class Wallet(Base):
    __tablename__ = "wallets"
    __table_args__ = (
        Index("idx_wallets_user_created_id", "user_id", "created_at", "id"),
    )
    # ... columns ...
```

### Step 2: Use `PaginationHelper.paginate_query()` in your Repository

```python
from app.common.pagination import PaginationParams, PaginationHelper

class WalletRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_wallets_paginated(self, user_id: UUID, params: PaginationParams):
        query = self.db.query(Wallet).filter(Wallet.user_id == user_id)
        return PaginationHelper.paginate_query(
            query=query,
            model_class=Wallet,
            params=params,
            created_at_col=Wallet.created_at,
            id_col=Wallet.id
        )
```

### Step 3: Wire Controller and Router with `PaginationParams`

```python
# Router
@router.get("/user/{user_id}", response_model=PaginatedResponse[WalletResponse])
def get_user_wallets(
    user_id: UUID,
    params: PaginationParams = Depends(),
    controller: WalletController = Depends(get_wallet_controller)
):
    return controller.get_user_wallets(user_id, params)
```

---

## 4. Query & Index Performance Benchmark

### Why Keyset Pagination Scales to Millions of Rows

1. **Direct Index Seeking vs Table Scanning**:
   - **Limit-Offset (`OFFSET 100000 LIMIT 20`)**: Database must traverse and discard 100,000 rows in memory. Performance degrades linearly $O(N)$ as page depth increases.
   - **Keyset Cursor (`WHERE (created_at, id) < (cursor_time, cursor_id)`)**: Database uses standard B-Tree index lookup to jump directly to the target record location in logarithmic time **$O(\log N)$**.

2. **Peeking `limit + 1` Rows**:
   - For cursor requests, `PaginationHelper` fetches `limit + 1` items. If a `limit + 1`-th row is returned, `has_next` is set to `True`, completely avoiding an expensive `SELECT COUNT(*)` query over large datasets.

3. **Composite Index Alignment**:
   - Index `idx_transactions_user_created_id` (`user_id`, `created_at`, `id`) fulfills both the equality filter (`WHERE user_id = :id`), the range filter (`< cursor_time`), and the descending sort (`ORDER BY created_at DESC, id DESC`) without in-memory sorting (`filesort`).

---

## 5. Docker Container Execution Commands

All commands should be executed inside the container environment using `docker compose exec`:

```bash
# Run Database Migrations
docker compose exec api alembic revision --autogenerate -m "Add transaction pagination composite index"
docker compose exec api alembic upgrade head

# Inspect Logs
docker compose logs -f api
```
