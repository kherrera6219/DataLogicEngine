from __future__ import annotations

from backend.utils.exceptions import (
    CRITICAL_BOUNDARY_FAILURE_SEMANTICS,
    TYPED_ERROR_CLASSES,
    ErrorCategory,
    FailBehavior,
    OperationTimeoutError,
    ServiceUnavailableError,
    UKGException,
    ValidationError,
)


def test_taxonomy_has_one_typed_error_for_every_required_category():
    assert set(TYPED_ERROR_CLASSES) == set(ErrorCategory)
    assert all(
        issubclass(error_type, UKGException)
        for error_type in TYPED_ERROR_CLASSES.values()
    )


def test_typed_error_exposes_content_free_failure_metadata():
    error = ServiceUnavailableError(
        "Object storage is unavailable",
        capability="object_storage",
    )

    assert error.status_code == 503
    assert error.to_safe_dict() == {
        "code": "SERVICE_UNAVAILABLE",
        "category": "service",
        "fail_behavior": "fail_closed",
        "retryable": True,
        "capability": "object_storage",
    }


def test_timeout_is_retryable_but_still_fails_closed():
    error = OperationTimeoutError("Provider deadline exceeded")

    assert error.status_code == 504
    assert error.retryable is True
    assert error.fail_behavior is FailBehavior.CLOSED


def test_validation_error_retains_compatibility_details():
    error = ValidationError({"field": "missing"})

    assert error.details == {"errors": {"field": "missing"}}
    assert error.to_safe_dict()["category"] == "validation"


def test_critical_boundaries_have_rationale_and_terminal_state():
    assert CRITICAL_BOUNDARY_FAILURE_SEMANTICS
    assert {item.behavior for item in CRITICAL_BOUNDARY_FAILURE_SEMANTICS.values()} == {
        FailBehavior.CLOSED,
        FailBehavior.SOFT,
    }
    for semantics in CRITICAL_BOUNDARY_FAILURE_SEMANTICS.values():
        assert semantics.rationale.endswith(".")
        assert semantics.failure_state
