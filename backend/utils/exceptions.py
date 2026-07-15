"""Typed application failures and explicit critical-boundary semantics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ErrorCategory(str, Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    POLICY = "policy"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    MIGRATION = "migration"
    SERVICE = "service"
    PROVIDER = "provider"
    TOOL = "tool"
    TIMEOUT = "timeout"
    CANCELLATION = "cancellation"
    PERSISTENCE = "persistence"
    CORRUPTION = "corruption"
    INTERNAL_DEFECT = "internal_defect"


class FailBehavior(str, Enum):
    CLOSED = "fail_closed"
    SOFT = "fail_soft"


class UKGException(Exception):
    """Base class for failures safe to translate at an API/task boundary."""

    category = ErrorCategory.INTERNAL_DEFECT
    default_status_code = 500
    default_error_code = "INTERNAL_ERROR"
    default_fail_behavior = FailBehavior.CLOSED
    default_retryable = False

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        *,
        fail_behavior: FailBehavior | None = None,
        retryable: bool | None = None,
        capability: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code or self.default_status_code
        self.error_code = error_code or self.default_error_code
        self.details = details or {}
        self.fail_behavior = fail_behavior or self.default_fail_behavior
        self.retryable = self.default_retryable if retryable is None else retryable
        self.capability = capability

    def to_safe_dict(self) -> dict[str, Any]:
        """Return content-free failure metadata suitable for logs and APIs."""
        result: dict[str, Any] = {
            "code": self.error_code,
            "category": self.category.value,
            "fail_behavior": self.fail_behavior.value,
            "retryable": self.retryable,
        }
        if self.capability:
            result["capability"] = self.capability
        return result


class AuthenticationError(UKGException):
    category = ErrorCategory.AUTHENTICATION
    default_status_code = 401
    default_error_code = "UNAUTHORIZED"

    def __init__(
        self,
        message: str = "Authentication required",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)


class AuthorizationError(UKGException):
    category = ErrorCategory.AUTHORIZATION
    default_status_code = 403
    default_error_code = "FORBIDDEN"

    def __init__(
        self,
        message: str = "Permission denied",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)


class PolicyError(UKGException):
    category = ErrorCategory.POLICY
    default_status_code = 403
    default_error_code = "POLICY_DENIED"


class ValidationError(UKGException):
    category = ErrorCategory.VALIDATION
    default_status_code = 422
    default_error_code = "VALIDATION_ERROR"

    def __init__(
        self,
        errors: dict[str, Any],
        message: str = "Validation failed",
    ) -> None:
        super().__init__(message, details={"errors": errors})


class ConfigurationError(UKGException):
    category = ErrorCategory.CONFIGURATION
    default_status_code = 503
    default_error_code = "CONFIGURATION_INVALID"


class MigrationError(UKGException):
    category = ErrorCategory.MIGRATION
    default_status_code = 503
    default_error_code = "MIGRATION_FAILED"


class ServiceUnavailableError(UKGException):
    category = ErrorCategory.SERVICE
    default_status_code = 503
    default_error_code = "SERVICE_UNAVAILABLE"
    default_retryable = True


class ProviderError(UKGException):
    category = ErrorCategory.PROVIDER
    default_status_code = 502
    default_error_code = "PROVIDER_FAILURE"


class ToolExecutionError(UKGException):
    category = ErrorCategory.TOOL
    default_status_code = 502
    default_error_code = "TOOL_EXECUTION_FAILED"


class OperationTimeoutError(UKGException):
    category = ErrorCategory.TIMEOUT
    default_status_code = 504
    default_error_code = "OPERATION_TIMEOUT"
    default_retryable = True


class OperationCancelledError(UKGException):
    category = ErrorCategory.CANCELLATION
    default_status_code = 409
    default_error_code = "OPERATION_CANCELLED"


class PersistenceError(UKGException):
    category = ErrorCategory.PERSISTENCE
    default_status_code = 500
    default_error_code = "PERSISTENCE_FAILED"


class DataCorruptionError(UKGException):
    category = ErrorCategory.CORRUPTION
    default_status_code = 500
    default_error_code = "DATA_CORRUPTION"


class InternalDefectError(UKGException):
    category = ErrorCategory.INTERNAL_DEFECT
    default_status_code = 500
    default_error_code = "INTERNAL_DEFECT"


class ResourceNotFoundError(UKGException):
    """Compatibility error for a missing application resource."""

    category = ErrorCategory.VALIDATION
    default_status_code = 404
    default_error_code = "NOT_FOUND"

    def __init__(self, resource: str, identifier: Any = None) -> None:
        message = f"{resource} not found"
        if identifier is not None:
            message = f"{resource} with ID '{identifier}' not found"
        super().__init__(message)


class SecurityBreachError(PolicyError):
    """Compatibility error for a security policy rejection."""

    default_status_code = 400
    default_error_code = "SECURITY_VIOLATION"

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)


@dataclass(frozen=True)
class BoundaryFailureSemantics:
    behavior: FailBehavior
    rationale: str
    failure_state: str


CRITICAL_BOUNDARY_FAILURE_SEMANTICS: dict[str, BoundaryFailureSemantics] = {
    "authentication_and_authorization": BoundaryFailureSemantics(
        FailBehavior.CLOSED,
        "Identity or permission uncertainty must never grant access.",
        "request_rejected",
    ),
    "policy_and_safety_gates": BoundaryFailureSemantics(
        FailBehavior.CLOSED,
        "A missing or failed policy decision must not release work or content.",
        "request_blocked",
    ),
    "configuration_and_migration": BoundaryFailureSemantics(
        FailBehavior.CLOSED,
        "The runtime cannot claim readiness with invalid configuration or schema.",
        "capability_unavailable",
    ),
    "durable_mutation_and_artifact_write": BoundaryFailureSemantics(
        FailBehavior.CLOSED,
        "A failed write cannot be reported as committed or materialized.",
        "operation_failed_or_partial",
    ),
    "provider_and_tool_execution": BoundaryFailureSemantics(
        FailBehavior.CLOSED,
        "Upstream or tool failure cannot be replaced by fabricated output.",
        "typed_terminal_failure",
    ),
    "corruption_and_integrity": BoundaryFailureSemantics(
        FailBehavior.CLOSED,
        "Unverified data cannot be read, restored, or released as trusted.",
        "quarantined_or_recovery_required",
    ),
    "optional_external_telemetry": BoundaryFailureSemantics(
        FailBehavior.SOFT,
        "Opt-in telemetry failure must not interrupt local application work.",
        "telemetry_unavailable",
    ),
    "diagnostics_and_support_export": BoundaryFailureSemantics(
        FailBehavior.SOFT,
        "Export failure must be explicit while the local runtime remains usable.",
        "support_operation_failed",
    ),
    "metrics_observation": BoundaryFailureSemantics(
        FailBehavior.SOFT,
        "Metric recording is non-authoritative and must not change work results.",
        "metrics_degraded",
    ),
    "process_and_task_boundary": BoundaryFailureSemantics(
        FailBehavior.CLOSED,
        "The outer boundary may catch unknown defects only to preserve safe failure state.",
        "internal_defect_recorded",
    ),
}


TYPED_ERROR_CLASSES: dict[ErrorCategory, type[UKGException]] = {
    ErrorCategory.AUTHENTICATION: AuthenticationError,
    ErrorCategory.AUTHORIZATION: AuthorizationError,
    ErrorCategory.POLICY: PolicyError,
    ErrorCategory.VALIDATION: ValidationError,
    ErrorCategory.CONFIGURATION: ConfigurationError,
    ErrorCategory.MIGRATION: MigrationError,
    ErrorCategory.SERVICE: ServiceUnavailableError,
    ErrorCategory.PROVIDER: ProviderError,
    ErrorCategory.TOOL: ToolExecutionError,
    ErrorCategory.TIMEOUT: OperationTimeoutError,
    ErrorCategory.CANCELLATION: OperationCancelledError,
    ErrorCategory.PERSISTENCE: PersistenceError,
    ErrorCategory.CORRUPTION: DataCorruptionError,
    ErrorCategory.INTERNAL_DEFECT: InternalDefectError,
}
