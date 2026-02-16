"""
Runtime contract validation helpers for MCP connector tools.

The validator intentionally supports a focused JSON Schema subset used by
connector definitions (object/array/scalar types, required fields, enum,
additionalProperties, and basic numeric/string/array constraints).
"""

from __future__ import annotations

from typing import Any, Mapping


class ContractValidationError(ValueError):
    """Raised when a tool input/output violates its declared contract."""


def validate_tool_arguments(tool_name: str, schema: Mapping[str, Any] | None, arguments: Any) -> None:
    """Validate tool input payload against the declared input contract."""
    if not schema:
        return
    _validate_schema(arguments, dict(schema), path="arguments", tool_name=tool_name)


def validate_tool_result(tool_name: str, schema: Mapping[str, Any] | None, result: Any) -> None:
    """Validate tool result payload against the declared output contract."""
    if not schema:
        return
    _validate_schema(result, dict(schema), path="result", tool_name=tool_name)


def _validate_schema(value: Any, schema: dict[str, Any], *, path: str, tool_name: str) -> None:
    if not schema:
        return

    one_of = schema.get("oneOf")
    if isinstance(one_of, list) and one_of:
        _validate_one_of(value, one_of, path=path, tool_name=tool_name)
        return

    any_of = schema.get("anyOf")
    if isinstance(any_of, list) and any_of:
        _validate_any_of(value, any_of, path=path, tool_name=tool_name)
        return

    all_of = schema.get("allOf")
    if isinstance(all_of, list) and all_of:
        for child_schema in all_of:
            _validate_schema(value, dict(child_schema or {}), path=path, tool_name=tool_name)

    schema_type = schema.get("type")
    if schema_type is not None:
        _validate_type(value, schema_type, path=path, tool_name=tool_name)

    if "enum" in schema:
        enum_values = schema.get("enum") or []
        if value not in enum_values:
            _raise(
                tool_name,
                f"{path} must be one of {enum_values}; received {value!r}.",
            )

    if value is None:
        return

    if _matches_type(value, "string"):
        _validate_string_constraints(value, schema, path=path, tool_name=tool_name)
    if _matches_type(value, "number") or _matches_type(value, "integer"):
        _validate_numeric_constraints(value, schema, path=path, tool_name=tool_name)
    if _matches_type(value, "array"):
        _validate_array(value, schema, path=path, tool_name=tool_name)
    if _matches_type(value, "object"):
        _validate_object(value, schema, path=path, tool_name=tool_name)


def _validate_any_of(value: Any, schemas: list[Any], *, path: str, tool_name: str) -> None:
    errors: list[str] = []
    for candidate in schemas:
        try:
            _validate_schema(value, dict(candidate or {}), path=path, tool_name=tool_name)
            return
        except ContractValidationError as exc:
            errors.append(str(exc))
    _raise(
        tool_name,
        f"{path} failed anyOf validation ({len(errors)} schema options rejected).",
    )


def _validate_one_of(value: Any, schemas: list[Any], *, path: str, tool_name: str) -> None:
    success_count = 0
    for candidate in schemas:
        try:
            _validate_schema(value, dict(candidate or {}), path=path, tool_name=tool_name)
            success_count += 1
        except ContractValidationError:
            continue
    if success_count != 1:
        _raise(
            tool_name,
            f"{path} failed oneOf validation; expected exactly 1 schema match, got {success_count}.",
        )


def _validate_type(value: Any, expected: Any, *, path: str, tool_name: str) -> None:
    expected_types = expected if isinstance(expected, list) else [expected]
    normalized = [str(item).strip().lower() for item in expected_types if str(item).strip()]
    if not normalized:
        return
    if any(_matches_type(value, expected_type) for expected_type in normalized):
        return
    _raise(
        tool_name,
        f"{path} must be type {normalized}; received {type(value).__name__}.",
    )


def _matches_type(value: Any, expected_type: str) -> bool:
    expected_type = str(expected_type).strip().lower()
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return (isinstance(value, (int, float)) and not isinstance(value, bool))
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "null":
        return value is None
    return True


def _validate_object(value: Any, schema: dict[str, Any], *, path: str, tool_name: str) -> None:
    if not isinstance(value, dict):
        return

    required = schema.get("required") or []
    if isinstance(required, list):
        for key in required:
            if key not in value:
                _raise(tool_name, f"{path}.{key} is required.")

    properties = schema.get("properties")
    if not isinstance(properties, dict):
        properties = {}

    additional_properties = schema.get("additionalProperties", True)
    for key, nested_value in value.items():
        if key in properties:
            _validate_schema(
                nested_value,
                dict(properties.get(key) or {}),
                path=_path_join(path, key),
                tool_name=tool_name,
            )
            continue

        if additional_properties is False:
            _raise(tool_name, f"{_path_join(path, key)} is not allowed by contract.")

        if isinstance(additional_properties, dict):
            _validate_schema(
                nested_value,
                dict(additional_properties),
                path=_path_join(path, key),
                tool_name=tool_name,
            )


def _validate_array(value: Any, schema: dict[str, Any], *, path: str, tool_name: str) -> None:
    if not isinstance(value, list):
        return

    min_items = schema.get("minItems")
    if isinstance(min_items, int) and len(value) < min_items:
        _raise(tool_name, f"{path} must contain at least {min_items} items.")

    max_items = schema.get("maxItems")
    if isinstance(max_items, int) and len(value) > max_items:
        _raise(tool_name, f"{path} must contain at most {max_items} items.")

    items_schema = schema.get("items")
    if isinstance(items_schema, dict):
        for index, item_value in enumerate(value):
            _validate_schema(
                item_value,
                dict(items_schema),
                path=_path_join(path, index),
                tool_name=tool_name,
            )


def _validate_string_constraints(value: str, schema: dict[str, Any], *, path: str, tool_name: str) -> None:
    min_length = schema.get("minLength")
    if isinstance(min_length, int) and len(value) < min_length:
        _raise(tool_name, f"{path} must be at least {min_length} characters.")

    max_length = schema.get("maxLength")
    if isinstance(max_length, int) and len(value) > max_length:
        _raise(tool_name, f"{path} must be at most {max_length} characters.")


def _validate_numeric_constraints(value: Any, schema: dict[str, Any], *, path: str, tool_name: str) -> None:
    if isinstance(value, bool):
        return
    if not isinstance(value, (int, float)):
        return

    minimum = schema.get("minimum")
    if isinstance(minimum, (int, float)) and value < minimum:
        _raise(tool_name, f"{path} must be >= {minimum}.")

    maximum = schema.get("maximum")
    if isinstance(maximum, (int, float)) and value > maximum:
        _raise(tool_name, f"{path} must be <= {maximum}.")


def _path_join(path: str, component: Any) -> str:
    if isinstance(component, int):
        return f"{path}[{component}]"
    if not path:
        return str(component)
    return f"{path}.{component}"


def _raise(tool_name: str, message: str) -> None:
    raise ContractValidationError(f"Tool '{tool_name}' contract validation failed: {message}")

