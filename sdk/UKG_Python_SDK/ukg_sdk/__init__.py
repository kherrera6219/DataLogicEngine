"""UKG Python SDK — clients for the installed DataLogicEngine service.

Primary entrypoints:
- :class:`ukg_sdk.UKGClient` — sync HTTP API client
- :class:`ukg_sdk.UKGAsyncClient` — async HTTP API client
- :class:`ukg_sdk.UKGOverlay` — compatibility client for governed execution

"""

from .api_client import UKGClient, UKGAsyncClient, BaseClient
from .overlay import UKGOverlay
from .gateway import (
    AsyncGatewayClient,
    GatewayCapabilities,
    GatewayClient,
    GatewayJob,
    GatewayResult,
)
from .coordinates17 import CoordinateResolver17, Coordinate17

__version__ = "0.7.0"

try:
    from .dsqp import DSQPClient
except Exception:  # pragma: no cover - optional local package surface
    DSQPClient = None

__all__ = [
    # API Clients
    "UKGClient",
    "UKGAsyncClient",
    "BaseClient",
    "UKGOverlay",
    "GatewayClient",
    "AsyncGatewayClient",
    "GatewayResult",
    "GatewayJob",
    "GatewayCapabilities",
    # Coordinates
    "CoordinateResolver17",
    "Coordinate17",
    "DSQPClient",
]
