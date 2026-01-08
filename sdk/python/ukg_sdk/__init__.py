"""
UKG Python SDK

A typed Python client for the UKG Trace API.
"""

from ukg_sdk.client import UKGClient, UKGAsyncClient
from ukg_sdk.models import (
    Run,
    RunStatus,
    Stage,
    StageStatus,
    Artifact,
    Claim,
    ClaimStatus,
    Evidence,
    AxisVector,
    Persona,
    KAInvocation,
    PolicyDecision,
    MemoryEvent,
    TraceSpan,
    Export,
    ChatSession,
    ComplianceMapping,
)
from ukg_sdk.exceptions import (
    UKGError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)

__version__ = "1.0.0"
__all__ = [
    # Clients
    "UKGClient",
    "UKGAsyncClient",
    # Models
    "Run",
    "RunStatus",
    "Stage",
    "StageStatus",
    "Artifact",
    "Claim",
    "ClaimStatus",
    "Evidence",
    "AxisVector",
    "Persona",
    "KAInvocation",
    "PolicyDecision",
    "MemoryEvent",
    "TraceSpan",
    "Export",
    "ChatSession",
    "ComplianceMapping",
    # Exceptions
    "UKGError",
    "AuthenticationError",
    "NotFoundError",
    "RateLimitError",
    "ValidationError",
]
