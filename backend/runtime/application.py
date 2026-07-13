"""Application-instance runtime state and deterministic startup phases."""

from __future__ import annotations

import os
import re
import threading
import uuid
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path

from flask import Flask, current_app, has_request_context

from .metrics import RequestMetrics
from .models import RuntimePhase
from .ownership import RuntimeOwnership
from .supervisor import ServiceSupervisor

PhaseCallback = Callable[["ApplicationRuntime"], None]


class ApplicationRuntime:
    """Own lifecycle state for exactly one Flask application instance."""

    STARTUP_ORDER = (
        RuntimePhase.CONFIGURATION,
        RuntimePhase.PATHS_AND_ACL,
        RuntimePhase.RUNTIME_LOCK,
        RuntimePhase.SERVICE_SUPERVISOR,
        RuntimePhase.SERVICE_VERIFICATION,
        RuntimePhase.MIGRATIONS,
        RuntimePhase.STORES,
        RuntimePhase.ROUTES_AND_WORKERS,
        RuntimePhase.READINESS,
    )

    def __init__(
        self,
        app: Flask,
        *,
        runtime_root: str | Path,
        required_services: tuple[str, ...] = (),
    ) -> None:
        self.app = app
        self.instance_id = uuid.uuid4().hex
        self.runtime_root = Path(runtime_root).resolve()
        self.metrics = RequestMetrics()
        self.supervisor = ServiceSupervisor(required_services=required_services)
        self.ownership = RuntimeOwnership(
            self.runtime_root,
            version=str(app.config.get("APP_VERSION", "0.1.1")),
        )
        self.phase = RuntimePhase.CREATED
        self.phase_history: list[str] = [self.phase.value]
        self.failure_reason: str | None = None
        self.failure_detail: str | None = None
        self._callbacks: dict[RuntimePhase, list[PhaseCallback]] = {
            phase: [] for phase in self.STARTUP_ORDER
        }
        self._shutdown_callbacks: list[PhaseCallback] = []
        self._started_threads: set[threading.Thread] = set()
        self._bound_ports: set[int] = set()
        self._lock = threading.RLock()
        self._operation_lock = threading.Lock()
        self.active_operation: str | None = None
        self.system_events: list[str] = []
        self.shutdown_forced = False
        self.drain_timeout_seconds = max(
            0.0,
            float(app.config.get("DLE_DRAIN_TIMEOUT_SECONDS", 5.0)),
        )

    @property
    def started_threads(self) -> tuple[threading.Thread, ...]:
        with self._lock:
            return tuple(thread for thread in self._started_threads if thread.is_alive())

    @property
    def bound_ports(self) -> tuple[int, ...]:
        with self._lock:
            return tuple(sorted(self._bound_ports))

    def on_phase(self, phase: RuntimePhase, callback: PhaseCallback) -> None:
        if phase not in self._callbacks:
            raise ValueError(f"Unsupported startup phase: {phase}")
        self._callbacks[phase].append(callback)

    def on_shutdown(self, callback: PhaseCallback) -> None:
        self._shutdown_callbacks.append(callback)

    def track_thread(self, thread: threading.Thread) -> None:
        with self._lock:
            self._started_threads.add(thread)

    def track_port(self, port: int) -> None:
        with self._lock:
            self._bound_ports.add(int(port))

    def start(self) -> None:
        with self._lock:
            if self.phase == RuntimePhase.READY:
                return
            if self.phase not in {RuntimePhase.CREATED, RuntimePhase.STOPPED, RuntimePhase.FAILED}:
                raise RuntimeError(f"Runtime cannot start from phase {self.phase.value}")
            self.failure_reason = None
            self.failure_detail = None
            self.shutdown_forced = False

        inject_failure = str(self.app.config.get("DLE_FAIL_STARTUP_PHASE", "")).strip()
        try:
            for phase in self.STARTUP_ORDER:
                self._set_phase(phase)
                if inject_failure == phase.value:
                    raise RuntimeError(f"Injected startup failure at {phase.value}")
                for callback in self._callbacks[phase]:
                    callback(self)
            self._set_phase(RuntimePhase.READY)
        except Exception as exc:
            self.failure_reason = f"startup_failed:{self.phase.value}"
            message = str(exc).strip()
            self.failure_detail = (
                message[:120]
                if re.fullmatch(r"[a-z0-9_:,=.-]{1,120}", message)
                else "startup_phase_failed"
            )
            self.shutdown()
            self._set_phase(RuntimePhase.FAILED)
            raise RuntimeError(self.failure_reason) from exc

    def shutdown(self) -> None:
        with self._lock:
            if self.phase == RuntimePhase.STOPPED:
                return
        self._set_phase(RuntimePhase.DRAINING)
        # A lifecycle request is itself counted as in flight and must be allowed
        # to return the acknowledgement that Electron is waiting for.
        drain_floor = 1 if has_request_context() else 0
        self.shutdown_forced = not self.metrics.wait_for_inflight_at_most(
            drain_floor,
            self.drain_timeout_seconds,
        )
        for callback in reversed(self._shutdown_callbacks):
            try:
                callback(self)
            except Exception:
                continue
        self.supervisor.stop_all()
        self._set_phase(RuntimePhase.STOPPED)

    @contextmanager
    def exclusive_operation(self, name: str):
        """Drain new mutations while one lifecycle-sensitive operation runs."""
        if not self._operation_lock.acquire(blocking=False):
            raise RuntimeError(f"lifecycle_operation_busy:{self.active_operation or 'unknown'}")
        previous_phase = self.phase
        self.active_operation = name
        self._set_phase(RuntimePhase.DRAINING)
        try:
            yield
        finally:
            self.active_operation = None
            if self.phase == RuntimePhase.DRAINING:
                self._set_phase(previous_phase)
            self._operation_lock.release()

    def handle_system_event(self, event: str) -> None:
        """Apply the supported Windows power/session/time lifecycle contract."""
        normalized = str(event).strip().lower()
        supported = {
            "suspend",
            "hibernate",
            "resume",
            "logoff",
            "shutdown",
            "time_changed",
            "forced_termination",
        }
        if normalized not in supported:
            raise ValueError(f"unsupported_system_event:{normalized}")
        self.system_events.append(normalized)
        if normalized in {"suspend", "hibernate"}:
            if self.phase == RuntimePhase.READY:
                self._set_phase(RuntimePhase.DRAINING)
            return
        if normalized == "resume":
            for service in self.supervisor.names():
                self.supervisor.probe(service)
            if self.supervisor.required_ready():
                self._set_phase(RuntimePhase.READY)
            else:
                self.failure_reason = "resume_reconciliation_failed"
                self._set_phase(RuntimePhase.FAILED)
            return
        if normalized == "time_changed":
            return
        self.shutdown()

    def admits_request(self, method: str, path: str) -> bool:
        if path in {"/live", "/ready", "/health", "/api/v1/system/lifecycle/event"}:
            return True
        if method.upper() in {"GET", "HEAD", "OPTIONS", "TRACE"}:
            return True
        return self.phase == RuntimePhase.READY and self.active_operation is None

    def readiness(self) -> tuple[dict, int]:
        blockers = self.supervisor.required_blockers()
        service_snapshot = self.supervisor.snapshot()
        blocker_details = {
            name: service_snapshot[name].get("safe_reason") or service_snapshot[name]["state"]
            for name in blockers
        }
        if self.phase != RuntimePhase.READY:
            blockers = [f"runtime:{self.phase.value}", *blockers]
            blocker_details[f"runtime:{self.phase.value}"] = (
                self.failure_detail or self.failure_reason or self.phase.value
            )
        ready = not blockers
        return {
            "status": "ready" if ready else "not_ready",
            "phase": self.phase.value,
            "blockers": blockers,
            "blocker_details": blocker_details,
            "instance_id": self.instance_id,
        }, 200 if ready else 503

    def capabilities(self) -> dict:
        return {
            "instance_id": self.instance_id,
            "installation_id": (
                self.ownership.identity.installation_id
                if self.ownership.identity is not None
                else None
            ),
            "phase": self.phase.value,
            "services": self.supervisor.snapshot(),
            "active_operation": self.active_operation,
            "failure_detail": self.failure_detail,
            "system_events": list(self.system_events[-10:]),
            "shutdown_forced": self.shutdown_forced,
            "ready": self.phase == RuntimePhase.READY and self.supervisor.required_ready(),
        }

    def _set_phase(self, phase: RuntimePhase) -> None:
        with self._lock:
            self.phase = phase
            self.phase_history.append(phase.value)


def get_application_runtime(app: Flask | None = None) -> ApplicationRuntime:
    target = app or current_app
    runtime = target.extensions.get("dle_runtime")
    if not isinstance(runtime, ApplicationRuntime):
        raise RuntimeError("DataLogicEngine application runtime is not initialized")
    return runtime


def default_runtime_root(app: Flask) -> Path:
    configured = app.config.get("DLE_RUNTIME_ROOT") or os.environ.get("DLE_RUNTIME_ROOT")
    return Path(configured or app.instance_path).resolve()
