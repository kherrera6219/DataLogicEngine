"""Backend utility modules."""
from backend.utils.responses import (
    api_response,
    success_response,
    error_response,
    paginated_response,
    validation_error,
    not_found_error,
    forbidden_error,
    unauthorized_error,
    rate_limit_error,
    internal_error
)
from backend.utils.pagination import (
    PaginationParams,
    paginate_query,
    paginate_list,
    pagination_meta
)
from backend.utils.validation import (
    Validator,
    ValidationError as LegacyValidationError,
    validate_json_body,
    validate_query_params
)
from backend.utils.exceptions import (
    CRITICAL_BOUNDARY_FAILURE_SEMANTICS,
    TYPED_ERROR_CLASSES,
    UKGException,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    DataCorruptionError,
    ErrorCategory,
    FailBehavior,
    InternalDefectError,
    MigrationError,
    OperationCancelledError,
    OperationTimeoutError,
    PersistenceError,
    PolicyError,
    ProviderError,
    ResourceNotFoundError,
    SecurityBreachError,
    ServiceUnavailableError,
    ToolExecutionError,
    ValidationError
)

__all__ = [
    # Responses
    'api_response',
    'success_response',
    'error_response',
    'paginated_response',
    'validation_error',
    'not_found_error',
    'forbidden_error',
    'unauthorized_error',
    'rate_limit_error',
    'internal_error',
    # Pagination
    'PaginationParams',
    'paginate_query',
    'paginate_list',
    'pagination_meta',
    # Validation
    'Validator',
    'LegacyValidationError',
    'validate_json_body',
    'validate_query_params',
    # Exceptions
    'CRITICAL_BOUNDARY_FAILURE_SEMANTICS',
    'TYPED_ERROR_CLASSES',
    'UKGException',
    'AuthenticationError',
    'AuthorizationError',
    'ConfigurationError',
    'DataCorruptionError',
    'ErrorCategory',
    'FailBehavior',
    'InternalDefectError',
    'MigrationError',
    'OperationCancelledError',
    'OperationTimeoutError',
    'PersistenceError',
    'PolicyError',
    'ProviderError',
    'ResourceNotFoundError',
    'SecurityBreachError',
    'ServiceUnavailableError',
    'ToolExecutionError',
    'ValidationError'
]
