
import pytest
import os
import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# --- Setup Paths ---
ROOT_DIR = Path(__file__).parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# --- Discovery ---
KA_DIR = ROOT_DIR / "backend" / "knowledge_algorithms"
# Get only ka_*.py files
ka_files = sorted([f.name for f in KA_DIR.glob("ka_*.py") if f.name != "__init__.py"])

# --- Global Mocks ---
# These mocks prevent ImportError or RuntimeErrors when KAs import backend modules
sys.modules['extensions'] = MagicMock()
sys.modules['models'] = MagicMock()
sys.modules['backend.llm_gateway'] = MagicMock()
# Mock core if needed, though it exists on disk. 
# Some KAs might use backend.services
sys.modules['backend.services'] = MagicMock()

@pytest.fixture(scope="module", autouse=True)
def setup_mocks():
    """Ensure common dependencies are mocked for all KAs."""
    with patch('extensions.db'), \
         patch('models.User'), \
         patch('models.ChatSession'):
        yield

@pytest.mark.parametrize("filename", ka_files)
def test_ka_structure_and_survival(filename):
    """
    Bulk verify that:
    1. KA Module can be imported (no SyntaxError, no missing deps).
    2. KA has a 'run' entry point.
    3. KA runs without unhandled crash (returns dict even on failure).
    """
    module_name = f"backend.knowledge_algorithms.{filename[:-3]}"
    
    print(f"Testing {module_name}...")
    
    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        pytest.fail(f"Failed to import {module_name}: {e}")
    except Exception as e:
        pytest.fail(f"Crash on import {module_name}: {e}")

    # Check for run function
    if not hasattr(module, "run"):
        pytest.fail(f"{filename} missing 'run(context)' function")
    
    # Prepare minimal context
    context = {
        "user_id": 1, 
        "session_id": "test_session",
        "mock": True,
        # Some KAs might look for input in context directly if not strict
    }
    
    # Execution Block
    try:
        # We expect KAs to return a result dict, OR handle internal errors gracefully.
        # If input is missing, they should return {'success': False, ...} rather than raise.
        # But if they raise ValidationError (Pydantic), that is also technically a 'crash' 
        # unless caught. ka_01 catches Exception in run() wrapper.
        
        result = module.run(context)
        
        assert isinstance(result, dict), f"{filename} returned {type(result)} instead of dict"
        assert "success" in result, f"{filename} result missing 'success' key"
        
        # We don't assert success==True because we gave empty input.
        # We just verify it survived.
        
    except Exception as e:
        pytest.fail(f"{filename} crashed during execution: {e}")
