"""Unit tests for pagination helpers."""

import pytest
from app.shared.pagination import PaginationParams, PaginatedResponse


def test_pagination_offset():
    p = PaginationParams(page=3, page_size=20)
    assert p.offset == 40
    assert p.limit == 20


def test_pagination_first_page():
    p = PaginationParams(page=1, page_size=10)
    assert p.offset == 0


def test_paginated_response_pages():
    params = PaginationParams(page=1, page_size=10)
    resp = PaginatedResponse.create(items=list(range(10)), total=95, params=params)
    assert resp.pages == 10
    assert resp.total == 95
    assert resp.page == 1


def test_paginated_response_single_page():
    params = PaginationParams(page=1, page_size=20)
    resp = PaginatedResponse.create(items=[1, 2, 3], total=3, params=params)
    assert resp.pages == 1


def test_paginated_response_exact_multiple():
    params = PaginationParams(page=2, page_size=5)
    resp = PaginatedResponse.create(items=list(range(5)), total=10, params=params)
    assert resp.pages == 2


def test_pagination_max_page_size_enforced():
    with pytest.raises(Exception):
        PaginationParams(page=1, page_size=999)
