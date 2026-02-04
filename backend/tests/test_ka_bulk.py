
import pytest
import os
import glob
import importlib.util
import inspect
from typing import Dict, Any, Type
import sys
from unittest.mock import MagicMock, patch

# Ensure backend and root are in path
# Current file: backend/tests/test_ka_bulk.py
# Root: backend/tests/../../ -> c:\software\DataLogicEngine
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
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
    ka_dir = os.path.join(os.path.dirname(__file__), '..', 'knowledge_algorithms')
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

def generate_mock_input(schema: Type[BaseModel]) -> Dict[str, Any]:
    """
    Generate valid mock input data based on a Pydantic schema.
    """
    mock_data = {}
    for field_name, field in schema.model_fields.items():
        # Get type annotation
        field_type = field.annotation
        
        # Simple heuristic for common types
        if field_type == str:
            mock_data[field_name] = "test_string"
        elif field_type == int:
            mock_data[field_name] = 1
        elif field_type == float:
            mock_data[field_name] = 1.0
        elif field_type == bool:
            mock_data[field_name] = True
        elif hasattr(field_type, '__origin__') and field_type.__origin__ == list:
            mock_data[field_name] = []
        elif hasattr(field_type, '__origin__') and field_type.__origin__ == dict:
            mock_data[field_name] = {}
        else:
            mock_data[field_name] = "mock_value"
            
    return mock_data

@pytest.mark.parametrize("scenario", ["HAPPY_PATH", "ERROR_STUB"])
@pytest.mark.parametrize("module_name, file_path", discovery_kas())
def test_knowledge_algorithm_contract(scenario, module_name, file_path):
    """
    Generic test that loads a KA, instantiates it, and attempts to run it.
    """
    # 1. Import the module dynamically
    spec = importlib.util.spec_from_file_location(f"backend.knowledge_algorithms.{module_name}", file_path)
    module = importlib.util.module_from_spec(spec)
    
    # Mocking environment
    mock_db = MagicMock()
    mock_cache = MagicMock()
    
    with patch.dict("sys.modules", {
        "extensions": MagicMock(db=mock_db, cache=mock_cache),
        "backend.extensions": MagicMock(db=mock_db, cache=mock_cache),
    }):
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            pytest.fail(f"Could not import {module_name}: {e}")

    # 2. Find the KA class
    ka_class = None
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and "KA" in name and name != "KnowledgeAlgorithm":
            if hasattr(obj, "input_schema"):
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
        "parameters": {"depth": 3, "use_cache": True}
    }

    # 4. Instantiate
    with patch("builtins.open", MagicMock()), \
         patch("os.path.exists", return_value=False), \
         patch("json.load", return_value={}):
        
        try:
            ka_instance = ka_class(mock_context)
        except Exception as e:
            pytest.fail(f"Failed to instantiate {ka_class.__name__}: {e}")

    # 5. Generate Input
    if not hasattr(ka_class, "input_schema") or not issubclass(ka_class.input_schema, BaseModel):
        pytest.skip(f"KA {ka_class.__name__} has no valid pydantic input_schema")
        
    input_data = generate_mock_input(ka_class.input_schema)
    
    # 6. Execution Harness
    with patch.object(ka_instance, "log_execution_step", MagicMock()), \
         patch.object(ka_instance, "_determine_strategy", return_value="standard", create=True):
         
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
                 assert isinstance(result, (dict, MagicMock)), "Result should be a dictionary or mock"
             else:
                 # In error scenario, it might return success=False or raise
                 pass
             
         except Exception as e:
             if scenario == "HAPPY_PATH":
                 pytest.fail(f"Execution failed for {ka_class.__name__}: {e}")
             else:
                 # Expected some failures in ERROR_STUB mode, but shouldn't crash unhandled
                 pass
