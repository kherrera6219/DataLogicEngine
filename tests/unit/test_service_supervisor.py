"""Phase 2 service-supervisor state and identity contracts."""

from backend.runtime import ServiceState, ServiceSupervisor


def test_supervisor_is_idempotent_and_returns_per_service_results():
    calls = {"start": 0, "stop": 0}

    def start():
        calls["start"] += 1
        return True

    def stop():
        calls["stop"] += 1
        return True

    supervisor = ServiceSupervisor(required_services=("postgresql",))
    supervisor.register(
        "postgresql",
        required=True,
        start=start,
        stop=stop,
        probe=lambda: (True, "dle-postgres"),
        expected_identity="dle-postgres",
    )

    first = supervisor.start("postgresql")
    second = supervisor.start("postgresql")
    assert first.success is True
    assert second.safe_reason == "already_ready"
    assert calls["start"] == 1
    assert supervisor.required_ready() is True

    stopped = supervisor.stop("postgresql")
    assert stopped.success is True
    assert calls["stop"] == 1


def test_foreign_port_identity_is_blocked_not_reported_ready():
    supervisor = ServiceSupervisor(required_services=("redis",))
    supervisor.register(
        "redis",
        required=True,
        start=lambda: True,
        probe=lambda: (True, "foreign-listener:127.0.0.1:6379"),
        expected_identity="datalogicengine:redis:owned",
    )

    supervisor.start("redis")
    status = supervisor.probe("redis")

    assert status.state == ServiceState.BLOCKED
    assert status.safe_reason == "foreign_service_identity"
    assert supervisor.required_ready() is False


def test_missing_required_service_blocks_readiness_with_safe_reason():
    supervisor = ServiceSupervisor(required_services=("minio",))
    supervisor.register("minio", required=True, installed=False)

    result = supervisor.start("minio")

    assert result.success is False
    assert result.state == ServiceState.BLOCKED
    assert result.safe_reason == "service_not_installed"
    assert supervisor.required_blockers() == ["minio"]


def test_dependency_order_and_budgets_are_published():
    supervisor = ServiceSupervisor()
    supervisor.register("postgresql", start=lambda: True)
    supervisor.register(
        "workers",
        start=lambda: True,
        depends_on=("postgresql",),
        start_timeout_seconds=12,
        stop_timeout_seconds=4,
    )
    supervisor.register("api_gateway", start=lambda: True, depends_on=("workers",))

    assert supervisor.startup_order() == ["postgresql", "workers", "api_gateway"]
    blocked = supervisor.start("workers")
    assert blocked.state == ServiceState.BLOCKED
    assert blocked.safe_reason == "dependency_not_ready:postgresql"

    supervisor.start("postgresql")
    assert supervisor.start("workers").success is True
    status = supervisor.snapshot()["workers"]
    assert status["start_timeout_seconds"] == 12
    assert status["stop_timeout_seconds"] == 4
