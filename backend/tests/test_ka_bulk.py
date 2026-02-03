import os
import pytest
import importlib.util
from typing import Dict, Any, List, Type, Union
from pydantic import BaseModel
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

def get_ka_files():
    ka_dir = os.path.join("backend", "knowledge_algorithms")
    files = [f for f in os.listdir(ka_dir) if f.startswith("ka_") and f.endswith(".py") and "master" not in f]
    return sorted(files)

def load_ka_module(filename: str):
    module_name = filename[:-3]
    module_path = os.path.join("backend", "knowledge_algorithms", filename)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@pytest.mark.parametrize("ka_file", get_ka_files())
def test_ka_contract(ka_file):
    """
    Dynamically tests each Knowledge Algorithm to ensure it fulfills the basic technical contract:
    1. It can be instantiated.
    2. It defines an input_schema.
    3. It handles execution without unhandled exceptions.
    """
    module = load_ka_module(ka_file)
    
    # Find the KA class in the module
    ka_class = None
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (isinstance(attr, type) and 
            issubclass(attr, KnowledgeAlgorithm) and 
            attr is not KnowledgeAlgorithm and
            not getattr(attr, "__abstractmethods__", None)): # Skip abstract classes
            ka_class = attr
            break
            
    assert ka_class is not None, f"No KnowledgeAlgorithm class found in {ka_file}"
    
    # Mock context and dependencies
    context = {
        "user_id": "test_user",
        "session_id": "test_sess",
        "query": "What is the capital of France?",
        "content": "Sample content for testing.",
        "records": [{"id": 1, "name": "Item 1"}],
        "parameters": {"depth": 1}
    }
    
    # Try to instantiate using positional argument to avoid naming conflicts (context vs config)
    try:
        instance = ka_class({})
    except Exception as e:
        pytest.fail(f"Failed to instantiate {ka_class.__name__} in {ka_file}: {e}")

    # Generate sample input based on schema
    input_schema: Type[BaseModel] = instance.input_schema
    sample_input = {}
    
    def get_default_for_annotation(annotation):
        # Handle Optional/Union
        origin = getattr(annotation, "__origin__", None)
        args = getattr(annotation, "__args__", [])
        
        if origin is Union:
            # Pick first non-None type
            for arg in args:
                if arg is not type(None):
                    return get_default_for_annotation(arg)
        
        if annotation == str: return "test"
        if annotation == int: return 1
        if annotation == float: return 1.0
        if annotation == bool: return True
        if origin is list: return []
        if origin is dict: return {}
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            return {f: get_default_for_annotation(val.annotation) for f, val in annotation.model_fields.items()}
        return None

    # Attempt to satisfy required fields with sensible defaults
    for field_name, field in input_schema.model_fields.items():
        if field.is_required():
            # Heuristic for required fields
            if "query" in field_name: sample_input[field_name] = context["query"]
            elif "content" in field_name: sample_input[field_name] = context["content"]
            elif "records" in field_name: sample_input[field_name] = context["records"]
            elif "metadata" in field_name: sample_input[field_name] = {}
            else:
                default = get_default_for_annotation(field.annotation)
                if default is not None:
                    sample_input[field_name] = default

    # Execute
    result = instance.run(sample_input)
    
    # Assertions
    assert isinstance(result, dict)
    assert "success" in result
    assert "execution_time_ms" in result
    # We don't strictly assert success=True because some KAs might fail due to lack of real data/services
    # but we DO assert it didn't crash with an E500 (Unhandled System Error)
    # but we DO assert it didn't crash with an E500 (Unhandled System Error)
    if not result["success"]:
        for error in result.get("errors", []):
            assert error["code"] != "E500", f"KA {ka_file} crashed with: {error['message']}\n{error.get('details')}"
