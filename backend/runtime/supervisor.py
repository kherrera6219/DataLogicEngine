"""One process-life owner for required and optional local services."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from threading import RLock

from .models import LifecycleResult, ServiceState, ServiceStatus

StartCallback = Callable[[], LifecycleResult | bool | None]
StopCallback = Callable[[], LifecycleResult | bool | None]
ProbeCallback = Callable[[], tuple[bool, str | None]]


class ServiceSupervisor:
    """Idempotent service registry with truthful typed lifecycle results."""

    def __init__(self, *, required_services: Iterable[str] = ()) -> None:
        required = set(required_services)
        self._lock = RLock()
        self._services: dict[str, ServiceStatus] = {
            name: ServiceStatus(name=name, required=True)
            for name in sorted(required)
        }
        self._start_callbacks: dict[str, StartCallback] = {}
        self._stop_callbacks: dict[str, StopCallback] = {}
        self._probe_callbacks: dict[str, ProbeCallback] = {}

    def register(
        self,
        name: str,
        *,
        required: bool = False,
        start: StartCallback | None = None,
        stop: StopCallback | None = None,
        probe: ProbeCallback | None = None,
        endpoint: str | None = None,
        expected_identity: str | None = None,
        installed: bool = True,
        depends_on: Iterable[str] = (),
        start_timeout_seconds: float = 30.0,
        stop_timeout_seconds: float = 15.0,
    ) -> None:
        with self._lock:
            status = self._services.setdefault(name, ServiceStatus(name=name))
            status.required = required
            status.endpoint = endpoint
            status.expected_identity = expected_identity
            status.dependencies = tuple(dict.fromkeys(depends_on))
            status.start_timeout_seconds = max(0.1, float(start_timeout_seconds))
            status.stop_timeout_seconds = max(0.1, float(stop_timeout_seconds))
            status.update(ServiceState.STOPPED if installed else ServiceState.NOT_INSTALLED)
            if start:
                self._start_callbacks[name] = start
            if stop:
                self._stop_callbacks[name] = stop
            if probe:
                self._probe_callbacks[name] = probe

    def start(self, name: str) -> LifecycleResult:
        with self._lock:
            status = self._require(name)
            if status.state == ServiceState.READY:
                return LifecycleResult(name, "start", True, status.state, "already_ready")
            if status.state == ServiceState.NOT_INSTALLED:
                reason = "service_not_installed"
                status.update(ServiceState.BLOCKED, safe_reason=reason)
                return LifecycleResult(name, "start", False, status.state, reason)
            blocked_dependencies = [
                dependency
                for dependency in status.dependencies
                if self._require(dependency).state != ServiceState.READY
            ]
            if blocked_dependencies:
                reason = f"dependency_not_ready:{','.join(blocked_dependencies)}"
                status.update(ServiceState.BLOCKED, safe_reason=reason)
                return LifecycleResult(name, "start", False, status.state, reason)
            callback = self._start_callbacks.get(name)
            if callback is None:
                reason = "start_not_configured"
                status.update(ServiceState.BLOCKED, safe_reason=reason)
                return LifecycleResult(name, "start", False, status.state, reason)
            status.update(ServiceState.STARTING)

        try:
            outcome = callback()
            if isinstance(outcome, LifecycleResult):
                with self._lock:
                    status.update(outcome.state, safe_reason=outcome.safe_reason)
                return outcome
            success = outcome is not False
            reason = None if success else "start_failed"
        except Exception:
            success = False
            reason = "start_failed"

        with self._lock:
            status.update(ServiceState.READY if success else ServiceState.FAILED, safe_reason=reason)
            return LifecycleResult(name, "start", success, status.state, reason)

    def stop(self, name: str) -> LifecycleResult:
        with self._lock:
            status = self._require(name)
            if status.state in {ServiceState.STOPPED, ServiceState.NOT_INSTALLED}:
                return LifecycleResult(name, "stop", True, status.state, "already_stopped")
            callback = self._stop_callbacks.get(name)
            status.update(ServiceState.STOPPING)

        try:
            outcome = callback() if callback else True
            if isinstance(outcome, LifecycleResult):
                with self._lock:
                    status.update(outcome.state, safe_reason=outcome.safe_reason)
                return outcome
            success = outcome is not False
            reason = None if success else "stop_failed"
        except Exception:
            success = False
            reason = "stop_failed"

        with self._lock:
            status.update(ServiceState.STOPPED if success else ServiceState.FAILED, safe_reason=reason)
            return LifecycleResult(name, "stop", success, status.state, reason)

    def start_all(self) -> dict[str, LifecycleResult]:
        return {name: self.start(name) for name in self.startup_order()}

    def stop_all(self) -> dict[str, LifecycleResult]:
        return {name: self.stop(name) for name in reversed(self.startup_order())}

    def startup_order(self) -> list[str]:
        """Return deterministic dependency order and reject dependency cycles."""
        with self._lock:
            remaining = {
                name: set(status.dependencies)
                for name, status in self._services.items()
            }
        ordered: list[str] = []
        while remaining:
            ready = sorted(
                name
                for name, dependencies in remaining.items()
                if dependencies.issubset(ordered)
            )
            if not ready:
                raise RuntimeError("service_dependency_cycle")
            for name in ready:
                ordered.append(name)
                remaining.pop(name)
        return ordered

    def probe(self, name: str) -> ServiceStatus:
        with self._lock:
            status = self._require(name)
            callback = self._probe_callbacks.get(name)
        if callback is None:
            return status
        try:
            healthy, identity = callback()
            with self._lock:
                identity_matches = (
                    not status.expected_identity
                    or status.expected_identity == identity
                    or bool(identity and identity.startswith(f"{status.expected_identity}:"))
                )
                if healthy and identity_matches:
                    status.update(ServiceState.READY, observed_identity=identity)
                elif healthy:
                    status.update(
                        ServiceState.BLOCKED,
                        safe_reason="foreign_service_identity",
                        observed_identity=identity,
                    )
                else:
                    status.update(ServiceState.FAILED, safe_reason="health_probe_failed")
        except Exception:
            with self._lock:
                status.update(ServiceState.FAILED, safe_reason="health_probe_failed")
        return status

    def snapshot(self) -> dict[str, dict]:
        with self._lock:
            return {name: status.to_dict() for name, status in self._services.items()}

    def update_status(
        self,
        name: str,
        state: ServiceState,
        *,
        safe_reason: str | None = None,
        observed_identity: str | None = None,
    ) -> ServiceStatus:
        """Publish a state transition from an application-owned service adapter."""
        with self._lock:
            status = self._require(name)
            status.update(
                state,
                safe_reason=safe_reason,
                observed_identity=observed_identity,
            )
            return status

    def required_ready(self) -> bool:
        with self._lock:
            required = [status for status in self._services.values() if status.required]
            return all(status.state == ServiceState.READY for status in required)

    def required_blockers(self) -> list[str]:
        with self._lock:
            return [
                status.name
                for status in self._services.values()
                if status.required and status.state != ServiceState.READY
            ]

    def names(self) -> list[str]:
        with self._lock:
            return sorted(self._services)

    def _require(self, name: str) -> ServiceStatus:
        try:
            return self._services[name]
        except KeyError as exc:
            raise KeyError(f"Unknown supervised service: {name}") from exc
