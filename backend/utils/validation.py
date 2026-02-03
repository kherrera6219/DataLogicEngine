"""
Input Validation Utilities.

Provides consistent validation for API request data.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Callable, TypeVar, Union
from functools import wraps
from flask import request, jsonify
import re
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ValidationError(Exception):
    """Raised when validation fails."""

    def __init__(self, errors: Union[Dict[str, List[str]], List[str]]):
        self.errors = errors
        super().__init__(str(errors))


class Validator:
    """Fluent validation builder for request data."""

    def __init__(self, data: Dict[str, Any]):
        self.data = data or {}
        self.errors: Dict[str, List[str]] = {}
        self._current_field: Optional[str] = None
        self._current_value: Any = None
        self._optional: bool = False

    def field(self, name: str, optional: bool = False) -> 'Validator':
        """Start validating a field."""
        self._current_field = name
        self._current_value = self.data.get(name)
        self._optional = optional
        return self

    def required(self) -> 'Validator':
        """Ensure field is present and not None."""
        if self._current_value is None:
            self._add_error(f"{self._current_field} is required")
        return self

    def string(self, min_length: int = None, max_length: int = None) -> 'Validator':
        """Validate as string with optional length constraints."""
        if self._should_skip():
            return self

        if not isinstance(self._current_value, str):
            self._add_error(f"{self._current_field} must be a string")
            return self

        if min_length and len(self._current_value) < min_length:
            self._add_error(f"{self._current_field} must be at least {min_length} characters")
        if max_length and len(self._current_value) > max_length:
            self._add_error(f"{self._current_field} must be at most {max_length} characters")

        return self

    def integer(self, min_value: int = None, max_value: int = None) -> 'Validator':
        """Validate as integer with optional range constraints."""
        if self._should_skip():
            return self

        if not isinstance(self._current_value, int) or isinstance(self._current_value, bool):
            self._add_error(f"{self._current_field} must be an integer")
            return self

        if min_value is not None and self._current_value < min_value:
            self._add_error(f"{self._current_field} must be at least {min_value}")
        if max_value is not None and self._current_value > max_value:
            self._add_error(f"{self._current_field} must be at most {max_value}")

        return self

    def boolean(self) -> 'Validator':
        """Validate as boolean."""
        if self._should_skip():
            return self

        if not isinstance(self._current_value, bool):
            self._add_error(f"{self._current_field} must be a boolean")

        return self

    def email(self) -> 'Validator':
        """Validate as email address."""
        if self._should_skip():
            return self

        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not isinstance(self._current_value, str) or not re.match(pattern, self._current_value):
            self._add_error(f"{self._current_field} must be a valid email address")

        return self

    def one_of(self, allowed: Set[Any], case_sensitive: bool = True) -> 'Validator':
        """Validate value is in allowed set."""
        if self._should_skip():
            return self

        value = self._current_value
        check_set = allowed

        if not case_sensitive and isinstance(value, str):
            value = value.lower()
            check_set = {v.lower() if isinstance(v, str) else v for v in allowed}

        if value not in check_set:
            self._add_error(f"{self._current_field} must be one of: {', '.join(map(str, allowed))}")

        return self

    def matches(self, pattern: str, message: str = None) -> 'Validator':
        """Validate string matches regex pattern."""
        if self._should_skip():
            return self

        if not isinstance(self._current_value, str) or not re.match(pattern, self._current_value):
            msg = message or f"{self._current_field} has invalid format"
            self._add_error(msg)

        return self

    def custom(self, validator: Callable[[Any], bool], message: str) -> 'Validator':
        """Apply custom validation function."""
        if self._should_skip():
            return self

        if not validator(self._current_value):
            self._add_error(message)

        return self

    def _should_skip(self) -> bool:
        """Check if validation should be skipped (optional field with no value)."""
        return self._optional and self._current_value is None

    def _add_error(self, message: str):
        """Add an error for the current field."""
        if self._current_field not in self.errors:
            self.errors[self._current_field] = []
        self.errors[self._current_field].append(message)

    def validate(self) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Complete validation and return results.

        Returns:
            Tuple of (is_valid, errors_dict)
        """
        return len(self.errors) == 0, self.errors

    def validate_or_raise(self) -> Dict[str, Any]:
        """
        Complete validation, raising ValidationError if invalid.

        Returns:
            Validated data dictionary

        Raises:
            ValidationError: If validation fails
        """
        is_valid, errors = self.validate()
        if not is_valid:
            raise ValidationError(errors)
        return self.data


def validate_json_body(required_fields: List[str] = None) -> Callable:
    """
    Decorator to validate JSON request body exists and has required fields.

    Args:
        required_fields: List of required field names

    Usage:
        @validate_json_body(['username', 'email'])
        def create_user():
            data = request.json  # Guaranteed to exist
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "INVALID_CONTENT_TYPE",
                        "message": "Content-Type must be application/json"
                    }
                }), 400

            data = request.get_json(silent=True)
            if data is None:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "INVALID_JSON",
                        "message": "Request body must be valid JSON"
                    }
                }), 400

            if required_fields:
                missing = [f for f in required_fields if f not in data or data[f] is None]
                if missing:
                    return jsonify({
                        "success": False,
                        "error": {
                            "code": "MISSING_FIELDS",
                            "message": f"Missing required fields: {', '.join(missing)}",
                            "details": {"missing_fields": missing}
                        }
                    }), 400

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_query_params(
    allowed: Dict[str, type] = None,
    required: List[str] = None
) -> Callable:
    """
    Decorator to validate query parameters.

    Args:
        allowed: Dict of param_name -> expected_type
        required: List of required parameter names

    Usage:
        @validate_query_params(
            allowed={'page': int, 'status': str},
            required=['status']
        )
        def list_items():
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            errors = []

            if required:
                missing = [p for p in required if p not in request.args]
                if missing:
                    errors.append(f"Missing required query parameters: {', '.join(missing)}")

            if allowed:
                for param, expected_type in allowed.items():
                    if param in request.args:
                        try:
                            # Explicitly cast to check type validity
                            val = request.args.get(param)
                            if val is not None:
                                expected_type(val)
                        except (ValueError, TypeError):
                            errors.append(f"Parameter '{param}' must be of type {expected_type.__name__}")

            if errors:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "INVALID_QUERY_PARAMS",
                        "message": "Invalid query parameters",
                        "details": {"errors": errors}
                    }
                }), 400

            return f(*args, **kwargs)
        return decorated_function
    return decorator
