"""UKG Python SDK (UKG/USKD) — consolidated release v0.3.1.

Primary entrypoints:
- :class:`ukg_sdk.api.TruthEngineAPI` — high-level TruthEngine + KA execution surface
- :class:`ukg_sdk.ka.executor.KAExecutor` — live KA execution map
- :class:`ukg_sdk.truth_engine.core.TruthEngine` — TruthEngine core + spec loader

"""

from .api import TruthEngineAPI
from .ka.executor import KAExecutor, KAExecutionContext, KAExecutionResult
from .truth_engine.core import TruthEngine, TruthEngineConfig, TruthResult

__all__ = [
    "TruthEngineAPI",
    "KAExecutor",
    "KAExecutionContext",
    "KAExecutionResult",
    "TruthEngine",
    "TruthEngineConfig",
    "TruthResult",
]

__version__ = "0.3.1"
