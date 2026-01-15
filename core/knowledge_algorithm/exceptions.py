"""
Standardized exception classes for the DataLogicEngine Knowledge Algorithm suite.
"""

class KAError(Exception):
    """Base exception for all Knowledge Algorithm related errors."""
    def __init__(self, message: str, error_code: str = "E000", details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

class KAValidationError(KAError):
    """Raised when input validation fails."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, error_code="E400", details=details)

class KAExecutionError(KAError):
    """Raised when an error occurs during _run_logic execution."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, error_code="E500", details=details)

class KAConfigError(KAError):
    """Raised when a Knowledge Algorithm is misconfigured."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, error_code="E401", details=details)

class KATimeoutError(KAError):
    """Raised when a Knowledge Algorithm exceeds its execution time limit."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, error_code="E408", details=details)

class KAIntegrationError(KAError):
    """Raised when a Knowledge Algorithm fails to interact with external systems."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, error_code="E502", details=details)
