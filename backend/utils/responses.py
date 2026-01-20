"""
Standardized API Response Utilities.

Provides consistent JSON response formatting across all API endpoints.
All responses follow the same structure for easier client integration.
"""

from datetime import datetime, UTC
from typing import Any, Optional, Dict, List, Union
from flask import jsonify, Response
import logging

logger = logging.getLogger(__name__)


def api_response(
    data: Any = None,
    message: str = "Operation successful",
    status_code: int = 200,
    meta: Optional[Dict[str, Any]] = None
) -> tuple[Response, int]:
    """
    Create a standardized success API response.

    Args:
        data: The response payload
        message: Human-readable message
        status_code: HTTP status code
        meta: Additional metadata (pagination, etc.)

    Returns:
        Tuple of (Response, status_code)
    """
    response = {
        "success": status_code < 400,
        "message": message,
        "data": data,
        "timestamp": datetime.now(UTC).isoformat()
    }

    if meta:
        response["meta"] = meta

    return jsonify(response), status_code


def success_response(
    data: Any = None,
    message: str = "Operation successful",
    status_code: int = 200
) -> tuple[Response, int]:
    """Shorthand for successful API response."""
    return api_response(data=data, message=message, status_code=status_code)


def error_response(
    message: str,
    status_code: int = 400,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> tuple[Response, int]:
    """
    Create a standardized error API response.

    Args:
        message: Human-readable error message
        status_code: HTTP status code (4xx or 5xx)
        error_code: Machine-readable error code
        details: Additional error details

    Returns:
        Tuple of (Response, status_code)
    """
    response = {
        "success": False,
        "error": {
            "code": error_code or _status_to_error_code(status_code),
            "message": message
        },
        "timestamp": datetime.now(UTC).isoformat()
    }

    if details:
        response["error"]["details"] = details

    return jsonify(response), status_code


def paginated_response(
    items: List[Any],
    total: int,
    page: int,
    per_page: int,
    message: str = "Data retrieved successfully"
) -> tuple[Response, int]:
    """
    Create a paginated API response.

    Args:
        items: List of items for current page
        total: Total number of items across all pages
        page: Current page number (1-indexed)
        per_page: Items per page
        message: Human-readable message

    Returns:
        Tuple of (Response, status_code)
    """
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    meta = {
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

    return api_response(data=items, message=message, meta=meta)


def validation_error(
    errors: Union[Dict[str, List[str]], List[str]],
    message: str = "Validation failed"
) -> tuple[Response, int]:
    """
    Create a validation error response.

    Args:
        errors: Dictionary of field->errors or list of error messages
        message: Human-readable message

    Returns:
        Tuple of (Response, status_code)
    """
    return error_response(
        message=message,
        status_code=422,
        error_code="VALIDATION_ERROR",
        details={"validation_errors": errors}
    )


def not_found_error(
    resource: str = "Resource",
    identifier: Any = None
) -> tuple[Response, int]:
    """Create a 404 not found error response."""
    msg = f"{resource} not found"
    if identifier:
        msg = f"{resource} with ID '{identifier}' not found"
    return error_response(msg, status_code=404, error_code="NOT_FOUND")


def forbidden_error(
    message: str = "You do not have permission to perform this action"
) -> tuple[Response, int]:
    """Create a 403 forbidden error response."""
    return error_response(message, status_code=403, error_code="FORBIDDEN")


def unauthorized_error(
    message: str = "Authentication required"
) -> tuple[Response, int]:
    """Create a 401 unauthorized error response."""
    return error_response(message, status_code=401, error_code="UNAUTHORIZED")


def rate_limit_error(
    retry_after: int = 60
) -> tuple[Response, int]:
    """Create a 429 rate limit error response."""
    return error_response(
        message=f"Rate limit exceeded. Please try again in {retry_after} seconds.",
        status_code=429,
        error_code="RATE_LIMIT_EXCEEDED",
        details={"retry_after": retry_after}
    )


def internal_error(
    message: str = "An internal error occurred. Please try again later."
) -> tuple[Response, int]:
    """Create a 500 internal server error response."""
    return error_response(message, status_code=500, error_code="INTERNAL_SERVER_ERROR")


def _status_to_error_code(status_code: int) -> str:
    """Convert HTTP status code to error code string."""
    codes = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT"
    }
    return codes.get(status_code, "ERROR")
