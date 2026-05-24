"""UKG Python SDK (UKG/USKD) — consolidated release v0.4.0.

Primary entrypoints:
- :class:`ukg_sdk.UKGClient` — sync HTTP API client
- :class:`ukg_sdk.UKGAsyncClient` — async HTTP API client
- :class:`ukg_sdk.UKGOverlay` — LLM orchestration overlay
- :class:`ukg_sdk.TruthEngineAPI` — high-level TruthEngine + KA execution surface
- :class:`ukg_sdk.KAExecutor` — live KA execution map
- :class:`ukg_sdk.TruthEngine` — TruthEngine core + spec loader
- :class:`ukg_sdk.WorkflowRunner` — tier-based workflow routing

"""

from .api import TruthEngineAPI
from .api_client import UKGClient, UKGAsyncClient, BaseClient
from .ka.executor import KAExecutor, KAExecutionContext, KAExecutionResult
from .truth_engine.core import TruthEngine, TruthEngineConfig, TruthResult
from .overlay import UKGOverlay
from .workflow import WorkflowRunner, ComplexityTier, WorkflowConfig
from .coordinates17 import CoordinateResolver17, Coordinate

__version__ = "0.4.0"

__all__ = [
    # API Clients
    "UKGClient",
    "UKGAsyncClient",
    "BaseClient",
    # Core Systems
    "TruthEngineAPI",
    "UKGOverlay",
    "WorkflowRunner",
    "ComplexityTier",
    "WorkflowConfig",
    # Knowledge Agents
    "KAExecutor",
    "KAExecutionContext",
    "KAExecutionResult",
    # Truth Engine
    "TruthEngine",
    "TruthEngineConfig",
    "TruthResult",
    # Coordinates
    "CoordinateResolver17",
    "Coordinate",
]
