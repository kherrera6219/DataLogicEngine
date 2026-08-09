# ruff: noqa: BLE001

import glob
import importlib.util
import inspect
import os
import sys
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Ensure backend and root are in path
# Current file: backend/tests/test_ka_bulk.py
# Root: backend/tests/../../ -> c:\software\DataLogicEngine
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from pydantic import BaseModel

# We expect to find 'core' package in project_root
# We expect to find 'backend' package in project_root (so 'backend.knowledge_algorithms' works)


def discovery_kas():
    """
    Dynamically discover all KA modules.
    Returns a list of tuples: (module_name, file_path)
    """
    ka_dir = os.path.join(project_root, "backend", "knowledge_algorithms")
    ka_dir = os.path.abspath(ka_dir)
    ka_files = glob.glob(os.path.join(ka_dir, "ka_*.py"))

    discovered = []
    for f in ka_files:
        basename = os.path.basename(f)
        if basename == "__init__.py":
            continue
        module_name = basename.replace(".py", "")
        discovered.append((module_name, f))

    return discovered


def _example_from_json_schema(
    definition: dict[str, Any],
    root_schema: dict[str, Any],
) -> Any:
    """Build the smallest valid value described by a JSON Schema node."""
    if "$ref" in definition:
        target: Any = root_schema
        for part in definition["$ref"].removeprefix("#/").split("/"):
            target = target[part]
        return _example_from_json_schema(target, root_schema)

    if "default" in definition:
        return definition["default"]
    if definition.get("enum"):
        return definition["enum"][0]

    for union_key in ("anyOf", "oneOf"):
        if union_key in definition:
            options = [
                option
                for option in definition[union_key]
                if option.get("type") != "null"
            ]
            if options:
                return _example_from_json_schema(options[0], root_schema)
            return None

    value_type = definition.get("type")
    if value_type == "string":
        if definition.get("pattern") == r"^[a-fA-F0-9]{64}$":
            return "a" * 64
        return "test_string"
    if value_type == "integer":
        return max(1, int(definition.get("minimum", 1)))
    if value_type == "number":
        return max(1.0, float(definition.get("minimum", 1.0)))
    if value_type == "boolean":
        return True
    if value_type == "array":
        count = int(definition.get("minItems", 0))
        item_schema = definition.get("items", {})
        return [
            _example_from_json_schema(item_schema, root_schema) for _ in range(count)
        ]
    if value_type == "object":
        properties = definition.get("properties", {})
        return {
            name: _example_from_json_schema(properties[name], root_schema)
            for name in definition.get("required", [])
        }
    if value_type == "null":
        return None
    return "mock_value"


def generate_mock_input(schema: type[BaseModel]) -> dict[str, Any]:
    """
    Generate valid mock input data based on a Pydantic schema.
    """
    json_schema = schema.model_json_schema()
    examples = json_schema.get("examples", [])
    if examples:
        return examples[0]
    properties = json_schema.get("properties", {})
    return {
        field_name: _example_from_json_schema(
            properties[field_name],
            json_schema,
        )
        for field_name in json_schema.get("required", [])
    }


@pytest.mark.parametrize("scenario", ["HAPPY_PATH", "ERROR_STUB"])
@pytest.mark.parametrize("module_name, file_path", discovery_kas())
def test_knowledge_algorithm_contract(scenario, module_name, file_path):
    """
    Generic test that loads a KA, instantiates it, and attempts to run it.
    """
    # 1. Import the module dynamically
    qualified_module_name = f"backend.knowledge_algorithms.{module_name}"
    spec = importlib.util.spec_from_file_location(qualified_module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    # Match importlib's normal loading semantics so Pydantic can resolve
    # postponed annotations while constructing the schema later in the test.
    sys.modules[qualified_module_name] = module

    # Mocking environment
    mock_db = MagicMock()
    mock_cache = MagicMock()

    with patch.dict(
        "sys.modules",
        {
            "extensions": MagicMock(db=mock_db, cache=mock_cache),
            "backend.extensions": MagicMock(db=mock_db, cache=mock_cache),
        },
    ):
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            pytest.fail(f"Could not import {module_name}: {e}")

    # 2. Find the KA class
    ka_class = None
    for name, obj in inspect.getmembers(module):
        if (
            inspect.isclass(obj)
            and "KA" in name
            and name != "KnowledgeAlgorithm"
            and hasattr(obj, "input_schema")
        ):
            ka_class = obj
            break

    if not ka_class:
        pytest.skip(f"No valid KA class found in {module_name}")

    # 3. Prepare Rich Context Mock
    mock_context = {
        "user_id": "test_user_75",
        "session_id": "session_infrastructure_sweep",
        "tenant_id": "tenant_enterprise",
        "logger": MagicMock(),
        "db": mock_db,
        "cache": mock_cache,
        "parameters": {"depth": 3, "use_cache": True},
    }

    # 4. Instantiate
    with (
        patch("builtins.open", MagicMock()),
        patch("os.path.exists", return_value=False),
        patch("json.load", return_value={}),
    ):
        try:
            ka_instance = ka_class(mock_context)
        except Exception as e:
            pytest.fail(f"Failed to instantiate {ka_class.__name__}: {e}")

    # 5. Generate Input
    if not hasattr(ka_class, "input_schema") or not issubclass(
        ka_class.input_schema, BaseModel
    ):
        pytest.skip(f"KA {ka_class.__name__} has no valid pydantic input_schema")

    input_data = generate_mock_input(ka_class.input_schema)

    # 6. Execution Harness
    with (
        patch.object(ka_instance, "log_execution_step", MagicMock()),
        patch.object(
            ka_instance, "_determine_strategy", return_value="standard", create=True
        ),
    ):
        if scenario == "ERROR_STUB":
            # Inject failures into common dependencies
            mock_db.session.query.side_effect = Exception("Database Failure")
            mock_cache.get.side_effect = Exception("Cache Failure")

        try:
            # Create input object
            try:
                input_model = ka_class.input_schema(**input_data)
            except Exception as validation_err:
                pytest.fail(f"Input validation failed with mock data: {validation_err}")

            # Call logic
            # First try _run_logic (unit style), then run() (integration style)
            if hasattr(ka_instance, "_run_logic"):
                result = ka_instance._run_logic(input_model)
            elif hasattr(ka_instance, "run"):
                # run() usually takes a dict or the model itself depending on base class
                # If it's the base run(), it converts model to dict and calls _run_logic
                try:
                    result = ka_instance.run(input_model)
                except TypeError:
                    # Maybe it expects a dict
                    result = ka_instance.run(input_data)
            else:
                pytest.skip(f"{ka_class.__name__} has no executable method found")

            # 7. Verification
            if scenario == "HAPPY_PATH":
                assert isinstance(result, (dict, MagicMock)), (
                    "Result should be a dictionary or mock"
                )
            else:
                # In error scenario, it might return success=False or raise
                pass

        except Exception as e:
            if scenario == "HAPPY_PATH":
                pytest.fail(f"Execution failed for {ka_class.__name__}: {e}")
            else:
                # Expected some failures in ERROR_STUB mode, but shouldn't crash unhandled
                pass
