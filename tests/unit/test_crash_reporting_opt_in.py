from backend.observability.crash_reporting import initialize_crash_reporting


def test_external_crash_reporting_requires_explicit_opt_in():
    state = initialize_crash_reporting(
        enabled=False,
        dsn="https://public@example.invalid/1",
        environment="testing",
        release="test",
    )

    assert state["initialized"] is True
    assert state["enabled"] is False
    assert state["provider"] == "none"
    assert state["init_error"] == "external_telemetry_opt_in_required"


def test_local_crash_ids_need_no_external_provider():
    state = initialize_crash_reporting(
        enabled=False,
        dsn=None,
        environment="testing",
        release="test",
    )

    assert state["enabled"] is False
    assert state["provider"] == "none"
    assert state["init_error"] is None
