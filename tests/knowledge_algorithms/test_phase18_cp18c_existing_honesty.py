from backend.knowledge_algorithms.controller import CanonicalKAController


def execute(ka_id: str, payload: dict):
    return CanonicalKAController().execute(
        {"ka_id": ka_id, "mode": "evaluation", "input": payload}
    )


def test_ka_008_self_critique_is_deterministic_and_accuracy_honest():
    payload = {
        "query": "Explain encryption controls",
        "output_content": "Encryption controls protect stored data.",
        "required_points": ["encryption controls", "stored data"],
    }

    first = execute("KA-008", payload)
    second = execute("KA-008", payload)

    assert first.success is True
    assert first.output == second.output
    assert first.output["rubric_scores"]["accuracy"] is None
    assert first.output["assessment_complete"] is False
    assert first.output["is_sufficient"] is False


def test_ka_012_persona_simulation_emits_review_findings_not_fake_claims():
    result = execute(
        "KA-012",
        {
            "query": "Assess a regulated encryption deployment",
            "active_personas": ["knowledge", "regulatory"],
        },
    )

    assert result.success is True
    assert len(result.output["persona_findings"]) == 2
    assert result.output["claims"] == []
    assert all(
        row["measurement_status"] == "not_measured" and row["confidence"] is None
        for row in result.output["persona_findings"]
    )


def test_ka_028_point_of_view_expansion_has_stable_ranked_selection():
    payload = {
        "query": "Evaluate usability and return on investment",
        "context": {"audience": "end users and investors"},
        "existing_personas": ["competitor"],
    }

    first = execute("KA-028", payload)
    second = execute("KA-028", payload)

    assert first.success is True
    assert first.output == second.output
    assert "competitor" not in first.output["selection_order"]
    assert first.output["deterministic"] is True


def test_ka_091_visualization_builds_stable_spec_without_fake_asset():
    payload = {
        "viz_type": "graph",
        "title": "Evidence",
        "data": {"nodes": [{"id": "a"}], "edges": []},
    }

    first = execute("KA-091", payload)
    second = execute("KA-091", payload)

    assert first.success is True
    assert first.output == second.output
    assert first.output["rendered"] is False
    assert first.output["visualization"]["chart_id"].startswith("viz_")
    assert "assets" not in first.output["visualization"]


def test_ka_095_alerting_returns_proposal_without_delivery_claim():
    result = execute(
        "KA-095",
        {
            "event": "data plane unavailable",
            "level": "critical",
            "source": "readiness",
        },
    )

    assert result.success is True
    assert result.output["alert_recommended"] is True
    assert result.output["alert_triggered"] is False
    assert result.output["delivery_receipt"] is None
    assert result.output["effect_proposal"]["status"] == "proposed"


def test_ka_097_auditing_returns_hash_chain_proposal_without_persistence_claim():
    payload = {
        "event_data": {"type": "config_change", "field": "provider"},
        "actor_id": "owner",
        "occurred_at": "2026-07-25T09:00:00Z",
    }

    first = execute("KA-097", payload)
    second = execute("KA-097", payload)

    assert first.success is True
    assert first.output["content_sha256"] == second.output["content_sha256"]
    assert first.output["persisted"] is False
    assert first.output["signed"] is False
    assert first.output["blockchain_anchored"] is False
    assert first.output["effect_proposal"]["status"] == "proposed"


def test_ka_098_profiling_aggregates_only_supplied_measurements():
    result = execute(
        "KA-098",
        {
            "target": "governed_request",
            "samples": [
                {
                    "duration_ms": 10,
                    "cpu_percent": 20,
                    "memory_mb": 100,
                    "calls": 2,
                    "hotspot": "retrieval",
                },
                {
                    "duration_ms": 30,
                    "cpu_percent": 40,
                    "memory_mb": 120,
                    "calls": 3,
                    "hotspot": "retrieval",
                },
            ],
        },
    )

    assert result.success is True
    assert result.output["metrics"]["duration_ms"]["mean"] == 20
    assert result.output["metrics"]["cpu_percent_mean"] == 30
    assert result.output["metrics"]["memory_mb_peak"] == 120
    assert result.output["metrics"]["calls_total"] == 5
    assert result.output["profile_dump"] is None


def test_ka_099_debugging_redacts_supplied_diagnostics_and_opens_no_port():
    result = execute(
        "KA-099",
        {
            "error_context": "provider failure",
            "frames": [
                {
                    "filename": "C:\\app\\worker.py",
                    "function": "run",
                    "line": 12,
                    "locals": {
                        "api_token": "secret-value",
                        "attempt": 2,
                    },
                }
            ],
            "system_metrics": {"credential_count": 1, "threads": 4},
        },
    )

    assert result.success is True
    assert result.output["remote_port_active"] is False
    assert result.output["snapshot"]["frames"][0]["filename"] == "worker.py"
    assert result.output["snapshot"]["frames"][0]["locals"]["api_token"] == "[REDACTED]"
    assert (
        result.output["snapshot"]["system_metrics"]["credential_count"] == "[REDACTED]"
    )


def test_ka_108_backup_strategy_returns_coordinated_backup_proposal_only():
    result = execute(
        "KA-108",
        {"target": "data_plane", "components": ["postgresql", "redis"]},
    )

    assert result.success is True
    assert result.output["backup_created"] is False
    assert result.output["backup_id"] is None
    assert result.output["verification_status"] == "not_run"
    assert result.output["effect_proposal"]["service"] == "operations_control_service"


def test_ka_110_integration_bus_returns_durable_outbox_proposal_only():
    result = execute(
        "KA-110",
        {
            "message": {"revision": 4},
            "topic": "knowledge_updates",
            "entity_id": "knowledge-1",
        },
    )

    assert result.success is True
    assert result.output["published"] is False
    assert result.output["acknowledge_receipt"] is False
    assert result.output["effect_proposal"]["service"] == "cross_store_outbox"


def test_ka_112_message_broker_returns_durable_job_proposal_only():
    result = execute(
        "KA-112",
        {
            "payload": {"simulation_id": "sim-1"},
            "queue": "background_tasks",
            "job_type": "simulation",
            "entity_id": "sim-1",
        },
    )

    assert result.success is True
    assert result.output["queued"] is False
    assert result.output["queue_active"] is None
    assert (
        result.output["effect_proposal"]["service"]
        == "postgresql_redis_job_coordinator"
    )
