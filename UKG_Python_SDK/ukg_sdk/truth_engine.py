"""Compatibility shim for TruthEngine.

Preferred imports:
- from ukg_sdk.truth_engine.core import TruthEngine
"""

from .truth_engine.core import TruthEngine, TruthEngineConfig, TruthResult  # noqa: F401
from .truth_engine.loader import load_truth_engine_from_specs  # noqa: F401
