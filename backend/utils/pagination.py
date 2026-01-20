"""
Pagination Utilities.

Provides consistent pagination handling across all list endpoints.
"""

from typing import Any, Dict, Optional, TypeVar, Generic
from flask import request
from flask_sqlalchemy.pagination import Pagination
from sqlalchemy.orm import Query

from backend.config.settings import settings


T = TypeVar('T')


class PaginationParams:
    """Validated pagination parameters from request."""

    def __init__(
        self,
        page: int = 1,
        per_page: int = None,
        max_per_page: int = None
    ):
        self.page = max(1, page)
        self.max_per_page = max_per_page or settings.MAX_PAGE_SIZE
        self.per_page = min(
            per_page or settings.DEFAULT_PAGE_SIZE,
            self.max_per_page
        )

    @classmethod
    def from_request(cls, max_per_page: int = None) -> 'PaginationParams':
        """
        Extract and validate pagination params from request query string.

        Args:
            max_per_page: Maximum allowed items per page (overrides settings)

        Returns:
            Validated PaginationParams instance
        """
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', settings.DEFAULT_PAGE_SIZE, type=int)

        # Also support 'limit' and 'offset' style
        if 'limit' in request.args:
            per_page = request.args.get('limit', settings.DEFAULT_PAGE_SIZE, type=int)
        if 'offset' in request.args:
            offset = request.args.get('offset', 0, type=int)
            page = (offset // per_page) + 1 if per_page > 0 else 1

        return cls(page=page, per_page=per_page, max_per_page=max_per_page)

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary."""
        return {
            "page": self.page,
            "per_page": self.per_page,
            "offset": (self.page - 1) * self.per_page
        }


def paginate_query(
    query: Query,
    params: Optional[PaginationParams] = None,
    error_out: bool = False
) -> Pagination:
    """
    Paginate a SQLAlchemy query.

    Args:
        query: SQLAlchemy query to paginate
        params: Pagination parameters (defaults to request params)
        error_out: Whether to raise 404 on empty page

    Returns:
        Flask-SQLAlchemy Pagination object
    """
    if params is None:
        params = PaginationParams.from_request()

    return query.paginate(
        page=params.page,
        per_page=params.per_page,
        error_out=error_out
    )


def paginate_list(
    items: list,
    params: Optional[PaginationParams] = None
) -> Dict[str, Any]:
    """
    Paginate an in-memory list.

    Args:
        items: List of items to paginate
        params: Pagination parameters (defaults to request params)

    Returns:
        Dictionary with paginated items and metadata
    """
    if params is None:
        params = PaginationParams.from_request()

    total = len(items)
    start = (params.page - 1) * params.per_page
    end = start + params.per_page

    page_items = items[start:end]
    total_pages = (total + params.per_page - 1) // params.per_page if params.per_page > 0 else 0

    return {
        "items": page_items,
        "pagination": {
            "page": params.page,
            "per_page": params.per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": params.page < total_pages,
            "has_prev": params.page > 1
        }
    }


def pagination_meta(pagination: Pagination) -> Dict[str, Any]:
    """
    Extract pagination metadata from Flask-SQLAlchemy Pagination object.

    Args:
        pagination: Flask-SQLAlchemy Pagination object

    Returns:
        Pagination metadata dictionary
    """
    return {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "total_pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev
    }
