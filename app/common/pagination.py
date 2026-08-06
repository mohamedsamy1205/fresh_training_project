from typing import Generic, List, Optional, TypeVar, Any
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Query
from sqlalchemy import desc

T = TypeVar("T")


class PaginationParams(BaseModel):
    """
    Query parameter dependency supporting Page and Limit pagination.
    Example: ?page=1&limit=20
    """
    page: int = Field(1, ge=1, description="Page number (1-based index)")
    limit: int = Field(20, ge=1, le=100, description="Items per page")


class PagePaginationMeta(BaseModel):
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Number of items per page")
    total: int = Field(..., description="Total count of matching records")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(False, description="Indicates if a next page exists")
    has_prev: bool = Field(False, description="Indicates if a previous page exists")


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)

    data: List[T]
    pagination: PagePaginationMeta


class PaginationHelper:
    """
    Reusable SQLAlchemy Page/Limit pagination helper.
    """
    @staticmethod
    def paginate_query(
        query: Query,
        model_class: Any,
        params: PaginationParams,
        created_at_col: Any = None,
        id_col: Any = None
    ) -> tuple[List[Any], PagePaginationMeta]:
        """
        Executes Page/Limit pagination on a SQLAlchemy query.
        Returns a tuple of (items, PagePaginationMeta).
        """
        created_at_col = created_at_col if created_at_col is not None else getattr(model_class, "created_at")
        id_col = id_col if id_col is not None else getattr(model_class, "id")

        page = params.page
        limit = params.limit

        total = query.count()
        total_pages = (total + limit - 1) // limit if total > 0 else 0

        offset = (page - 1) * limit
        items = query.order_by(desc(created_at_col), desc(id_col)).offset(offset).limit(limit).all()

        meta = PagePaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        return items, meta
