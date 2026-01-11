import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from knowledge_algorithms.ka_master_controller import get_controller

def test_controller():
    controller = get_controller()
    print(f"Loaded {len(controller.algorithms)} algorithms.")
    
    # Test normalization
    ka1_id = controller._normalize_ka_id("KA-1")
    print(f"Normalized KA-1 to {ka1_id}")
    
    # Check if KA-001 is loaded
    if "KA-001" in controller.algorithms:
        print("KA-001 found in registry")
        metadata = controller.algorithms["KA-001"].get("metadata")
        if metadata:
            print(f"KA-001 Metadata Name: {metadata.get('KA_Name')}")
            
    # Test loading a legacy KA
    success = controller.load_algorithm("KA-001")
    print(f"Loading KA-001: {success}")
    if success:
        alg = controller.algorithms["KA-001"]
        print(f"KA-001 loaded from: {alg.get('module_path')}.{alg.get('function_name')}")
        
    # Test loading a modern KA from KARegistry (KA-113)
    # We might need to register it first if it's not automatically discovered
    from backend.knowledge_algorithm.modules.ka113_complexity_router import KA113ComplexityRouter
    success = controller.load_algorithm("KA-113")
    print(f"Loading KA-113: {success}")
    if success:
        alg = controller.algorithms["KA-113"]
        print(f"KA-113 Is Class: {alg.get('is_class')}")
        
    # Execute KA-113
    result = controller.execute_algorithm("KA-113", {"query": "A complex regulatory question about blockchain."})
    print(f"KA-113 Result: {result.get('output')}")

if __name__ == "__main__":
    test_controller()
