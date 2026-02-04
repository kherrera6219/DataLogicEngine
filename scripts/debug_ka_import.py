
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# Setup Path equivalent to test
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

print(f"Sys Path[0]: {sys.path[0]}")

# Mock logic
try:
    mock_core = MagicMock()
    sys.modules["core"] = mock_core
    sys.modules["core.knowledge_algorithm"] = mock_core.knowledge_algorithm
    sys.modules["core.knowledge_algorithm.ka_base"] = mock_core.knowledge_algorithm.ka_base
    mock_core.knowledge_algorithm.ka_base.KnowledgeAlgorithm = MagicMock

    sys.modules["extensions"] = MagicMock()
    sys.modules["models"] = MagicMock()

    print("Attempting import...")
    from backend.knowledge_algorithms.ka_50_knowledge_integrity_validator import KA050KnowledgeIntegrityValidator
    print("Import successful!")
except Exception as e:
    print("IMPORT FAILED:")
    import traceback
    traceback.print_exc()
