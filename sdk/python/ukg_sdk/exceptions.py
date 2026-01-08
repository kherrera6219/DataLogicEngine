"""
Custom exceptions for the UKG SDK.
"""

from typing import Any, Optional


class UKGError(Exception):
    """Base exception for UKG SDK errors."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
    
    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(UKGError):
    """Raised when authentication fails (401)."""
    pass


class AuthorizationError(UKGError):
    """Raised when access is denied (403)."""
    pass


class NotFoundError(UKGError):
    """Raised when a resource is not found (404)."""
    pass


class ValidationError(UKGError):
    """Raised when request validation fails (400)."""
    
    def __init__(
        self,
        message: str,
        errors: Optional[list[dict[str, Any]]] = None,
        **kwargs: Any,
    ):
        super().__init__(message, **kwargs)
        self.errors = errors or []


class RateLimitError(UKGError):
    """Raised when rate limit is exceeded (429)."""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        **kwargs: Any,
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ServerError(UKGError):
    """Raised when server returns 5xx error."""
    pass


class TimeoutError(UKGError):
    """Raised when request times out."""
    pass


class ConnectionError(UKGError):
    """Raised when connection fails."""
    pass
