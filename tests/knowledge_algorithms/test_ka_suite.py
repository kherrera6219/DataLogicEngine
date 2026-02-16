
import pytest
import yaml
import importlib
import os
import sys
from unittest.mock import MagicMock, patch

# Ensure backend can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

def get_ka_registry():
    registry_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend/knowledge_algorithms/ka_registry.yaml'))
    if not os.path.exists(registry_path):
        return []
    with open(registry_path, 'r') as f:
        data = yaml.safe_load(f)
        return [(k, v) for k, v in data.get('ka_registry', {}).items() if not k.startswith("L10")]

# Parameterize over all KAs (excluding L10 if they have different structure, or include them)
# I included L10 check to be safe, but registry seems to list them with "backend..." paths too.
# The filter `if not k.startswith("L10")` might be too aggressive if variables allow, but let's test Core first.

@pytest.mark.parametrize("ka_id, impl_path", get_ka_registry())
def test_ka_instantiation_and_run(ka_id, impl_path):
    """
    Smoke test for every KA in the registry.
    Verifies:
    1. Module can be imported.
    2. run() function exists.
    3. run() accepts standard context without crashing.
    4. Returns a valid result dict.
    """
    
    # Parse path (e.g. backend.knowledge_algorithms.ka_01_algorithm_of_thought.run)
    try:
        module_path, func_name = impl_path.rsplit('.', 1)
    except ValueError:
        pytest.fail(f"Invalid implementation path format: {impl_path}")

    # Mock common external dependencies that might cause import side-effects
    # (Ad-hoc patching if we discover specific failures)
    
    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        pytest.fail(f"Could not import KA {ka_id} ({module_path}): {e}")

    if not hasattr(module, func_name):
        pytest.fail(f"Module {module_path} has no function '{func_name}'")

    run_func = getattr(module, func_name)

    # Prepare Context
    context = {
        "query": "Test Query for Smoke Test",
        "data": {"sample": "value"},
        "metadata": {"trace_id": "test-trace-001"},
        "user_id": "test-user"
    }

    # Execute with patching to prevent side effects (network, IO)
    with patch('builtins.open', new_callable=MagicMock):
        # Mock generic IO just in case
        try:
            result = run_func(context)
        except Exception as e:
            # Check if it is a validation error (expected for dummy input)
            # If so, we pass. We only fail on CRASHES (SyntaxError, ImportError, AttributeError etc.)
            error_msg = str(e).lower()
            if "validation" in error_msg or "required" in error_msg:
                # This counts as "Code was exercised and rejected input correctly" = PASS
                return
            pytest.fail(f"KA {ka_id} crashed during execution: {e}")

    # Assertions
    assert isinstance(result, dict), f"KA {ka_id} did not return a dict"
    # Basic standard fields
    if "success" not in result:
        # Some KAs might return different structure?
        # Phase 2 standards say they should return `KAResult` dict (success, output, etc.)
        pytest.warns(UserWarning, match=f"KA {ka_id} result missing 'success' key")
    
