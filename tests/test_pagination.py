import pytest
from app.common.pagination import (
    PaginationParams,
    PagePaginationMeta,
    PaginatedResponse
)


def test_pagination_params_defaults():
    params = PaginationParams()
    assert params.page == 1
    assert params.limit == 20


def test_pagination_params_custom():
    params = PaginationParams(page=2, limit=10)
    assert params.page == 2
    assert params.limit == 10


def test_page_pagination_meta_has_next_prev():
    meta = PagePaginationMeta(
        page=1,
        limit=20,
        total=45,
        total_pages=3,
        has_next=True,
        has_prev=False
    )
    assert meta.page == 1
    assert meta.has_next is True
    assert meta.has_prev is False

    meta_last = PagePaginationMeta(
        page=3,
        limit=20,
        total=45,
        total_pages=3,
        has_next=False,
        has_prev=True
    )
    assert meta_last.has_next is False
    assert meta_last.has_prev is True
