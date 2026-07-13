"""Typed runtime lifecycle and capability state."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class ServiceState(StrEnum):
    NOT_INSTALLED = "not_installed"
    STOPPED = "stopped"
    STARTING = "starting"
    MIGRATING = "migrating"
    READY = "ready"
    DEGRADED = "degraded"
    FAILED = "failed"
    STOPPING = "stopping"
    BLOCKED = "blocked"


class RuntimePhase(StrEnum):
    CREATED = "created"
    CONFIGURATION = "configuration"
    PATHS_AND_ACL = "paths_and_acl"
    RUNTIME_LOCK = "runtime_lock"
    SERVICE_SUPERVISOR = "service_supervisor"
    SERVICE_VERIFICATION = "service_verification"
    MIGRATIONS = "migrations"
    STORES = "stores"
    ROUTES_AND_WORKERS = "routes_and_workers"
    READINESS = "readiness"
    READY = "ready"
    DRAINING = "draining"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass(slots=True)
class ServiceStatus:
    name: str
    state: ServiceState = ServiceState.STOPPED
    required: bool = False
    safe_reason: str | None = None
    endpoint: str | None = None
    expected_identity: str | None = None
    observed_identity: str | None = None
    dependencies: tuple[str, ...] = ()
    start_timeout_seconds: float = 30.0
    stop_timeout_seconds: float = 15.0
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def update(
        self,
        state: ServiceState,
        *,
        safe_reason: str | None = None,
        observed_identity: str | None = None,
    ) -> None:
        self.state = state
        self.safe_reason = safe_reason
        if observed_identity is not None:
            self.observed_identity = observed_identity
        self.updated_at = datetime.now(UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["state"] = self.state.value
        return result


@dataclass(frozen=True, slots=True)
class LifecycleResult:
    service: str
    action: str
    success: bool
    state: ServiceState
    safe_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["state"] = self.state.value
        return result
