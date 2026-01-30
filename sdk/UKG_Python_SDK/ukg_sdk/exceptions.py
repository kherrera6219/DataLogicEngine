class UKGError(Exception):
    """Base error for ukg_sdk."""


class UKGHTTPError(UKGError):
    def __init__(self, status_code: int, message: str, detail=None):
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code
        self.message = message
        self.detail = detail


class UKGConfigError(UKGError):
    """Raised for invalid/missing configuration."""


class UKGValidationError(UKGError):
    """Raised when local validation fails."""


class UKGNotFoundError(UKGError):
    """Raised for missing registry keys or files."""


class UKGWorkflowError(UKGError):
    """Raised when workflow orchestration fails."""


# Added for compatibility with api_client.py
class AuthenticationError(UKGHTTPError):
    """Raised when authentication fails (401)."""


class AuthorizationError(UKGHTTPError):
    """Raised when authorization fails (403)."""


class NotFoundError(UKGHTTPError):
    """Raised when a resource is not found (404)."""


class RateLimitError(UKGHTTPError):
    """Raised when rate limit is exceeded (429)."""


class ServerError(UKGHTTPError):
    """Raised when the server returns an error (5xx)."""


class ValidationError(UKGError):
    """Raised when validation fails."""
