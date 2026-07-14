class UKGError(Exception):
    """Base error for ukg_sdk."""


class UKGHTTPError(UKGError):
    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        detail=None,
        *,
        code: str | None = None,
    ):
        status_code = int(status_code or 0)
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code
        self.message = message
        self.detail = detail
        self.code = code


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


class ConflictError(UKGHTTPError):
    """Raised for idempotency or lifecycle conflicts (409)."""


class RateLimitError(UKGHTTPError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str,
        retry_after: int | None = None,
        status_code: int = 429,
        detail=None,
        *,
        code: str | None = None,
    ):
        super().__init__(message, status_code, detail, code=code)
        self.retry_after = retry_after


class ServerError(UKGHTTPError):
    """Raised when the server returns an error (5xx)."""


class ValidationError(UKGHTTPError):
    """Raised when validation fails."""

    def __init__(
        self,
        message: str,
        errors=None,
        status_code: int = 422,
        *,
        code: str | None = None,
    ):
        super().__init__(message, status_code, errors, code=code)
        self.errors = errors
