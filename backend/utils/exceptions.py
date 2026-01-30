"""
Standardized Exception Classes for UKG.

Provides a hierarchy of exceptions for granular error handling and reporting.
"""
from typing import Any, Dict, Optional


class UKGException(Exception):
    """Base exception for all internal UKG errors."""
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class AuthenticationError(UKGException):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication required", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, error_code="UNAUTHORIZED", details=details)


class AuthorizationError(UKGException):
    """Raised when a user lacks permission."""
    def __init__(self, message: str = "Permission denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, error_code="FORBIDDEN", details=details)


class ResourceNotFoundError(UKGException):
    """Raised when a requested resource is not found."""
    def __init__(self, resource: str, identifier: Any = None):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} with ID '{identifier}' not found"
        super().__init__(message, status_code=404, error_code="NOT_FOUND")


class SecurityBreachError(UKGException):
    """Raised when a security shield detects malicious activity."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, error_code="SECURITY_VIOLATION", details=details)


class ValidationError(UKGException):
    """Raised when input validation fails."""
    def __init__(self, errors: Dict[str, Any], message: str = "Validation failed"):
        super().__init__(message, status_code=422, error_code="VALIDATION_ERROR", details={"errors": errors})
