"""CP19-J authenticated KA product workflow qualification."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from backend.auth import api_decorators
from backend.knowledge_algorithms.product_workflow import (
    KAProductRunRunner,
    KAProductWorkflowError,
    _validate_applied_effect_receipts,
    confirm_and_queue_product_run,
    decrypt_product_result,
    plan_product_run,
    result_artifacts,
    result_effects,
    trace_summary,
    validate_plan_request,
)
from extensions import db
from tests.conftest import create_test_user
from scripts.verify_phase19_cp19j_product_workflow import verify as verify_cp19j


def _install_product_key(
    app,
    monkeypatch,
    *,
    username: str,
    scopes: list[str],
    user_id: int | None = None,
):
    from models import ExternalAPIKey

    with app.app_context():
        if user_id is None:
            user_id = create_test_user(
                username=username,
                email=f"{username}@test.com",
            )
        key_id = uuid.uuid4()
        db.session.add(
            ExternalAPIKey(
                id=key_id,
                name=f"{username} key",
                key_prefix="ukg_phase19",
                key_hash=f"test-{key_id}",
                user_id=user_id,
                is_active=True,
                permissions={"scopes": scopes},
            )
        )
        db.session.commit()

    monkeypatch.setattr(
        api_decorators.ExternalAPIKey,
        "verify_key",
        staticmethod(lambda _key: db.session.get(ExternalAPIKey, key_id)),
    )
    return user_id, key_id


class _CapturedRunner:
    def __init__(self):
        self.submitted: list[str] = []

    def submit(self, run_id: str) -> None:
        self.submitted.append(run_id)

    def cancel(self, run) -> bool:
        run.cancellation_requested = True
        return True


def _plan_body(*, key: str, query: str = "Review this governed request"):
    return {
        "ka_id": "KA-004",
        "input": {"query": query},
        "mode": "production",
        "idempotency_key": key,
        "metadata": {"client": "cp19-j-test"},
        "budget": {
            "deadline_ms": 10_000,
            "max_dependency_executions": 8,
            "max_selected_algorithms": 8,
        },
    }


def test_product_routes_plan_replay_confirm_list_and_cancel(
    app,
    client,
    monkeypatch,
):
    _install_product_key(
        app,
        monkeypatch,
        username="cp19j_product_owner",
        scopes=["ka:read", "ka:plan", "ka:execute", "ka:cancel"],
    )
    captured = _CapturedRunner()
    monkeypatch.setattr(
        "backend.routes.ka_routes.get_ka_product_runner",
        lambda _app: captured,
    )
    headers = {"X-API-Key": "ukg_phase19_valid"}
    body = _plan_body(key="cp19j-plan-replay")

    planned = client.post("/api/v1/ka/runs/plan", json=body, headers=headers)

    assert planned.status_code == 201
    created = planned.get_json()
    run_id = created["run"]["run_id"]
    confirmation_token = created["confirmation_token"]
    assert created["success"] is True
    assert created["run"]["status"] == "planned"
    assert created["run"]["canonical_id"] == "KA-004"
    assert created["run"]["confirmation_required"] is True
    assert created["plan"]["selected_ids"] == ["KA-004"]
    assert confirmation_token
    assert "input" not in created["plan"]
    assert "client" not in planned.get_data(as_text=True)

    replay = client.post("/api/v1/ka/runs/plan", json=body, headers=headers)

    assert replay.status_code == 200
    assert replay.headers["Idempotent-Replay"] == "true"
    assert replay.get_json()["run"]["run_id"] == run_id
    assert replay.get_json()["confirmation_token"] == confirmation_token

    conflict = client.post(
        "/api/v1/ka/runs/plan",
        json=_plan_body(
            key="cp19j-plan-replay",
            query="A different governed request",
        ),
        headers=headers,
    )
    assert conflict.status_code == 409
    assert conflict.get_json()["code"] == "KA_IDEMPOTENCY_CONFLICT"

    wrong_confirmation = client.post(
        f"/api/v1/ka/runs/{run_id}/execute",
        json={"confirmation_token": "not-the-exact-token"},
        headers=headers,
    )
    assert wrong_confirmation.status_code == 403
    assert wrong_confirmation.get_json()["code"] == "KA_CONFIRMATION_REQUIRED"

    queued = client.post(
        f"/api/v1/ka/runs/{run_id}/execute",
        json={"confirmation_token": confirmation_token},
        headers=headers,
    )
    assert queued.status_code == 202
    assert queued.get_json()["run"]["status"] == "queued"
    assert captured.submitted == [run_id]

    listing = client.get("/api/v1/ka/runs", headers=headers)
    assert listing.status_code == 200
    assert [item["run_id"] for item in listing.get_json()["runs"]] == [run_id]

    cancelled = client.post(
        f"/api/v1/ka/runs/{run_id}/cancel",
        headers=headers,
    )
    assert cancelled.status_code == 202
    assert cancelled.get_json()["run"]["status"] == "cancelled"
    assert cancelled.get_json()["run"]["cancellation_requested"] is True

    _install_product_key(
        app,
        monkeypatch,
        username="cp19j_different_principal",
        scopes=["ka:read"],
    )
    isolated = client.get(
        f"/api/v1/ka/runs/{run_id}",
        headers={"X-API-Key": "ukg_phase19_other"},
    )
    assert isolated.status_code == 404


def test_product_routes_enforce_scope_and_principal_isolation(
    app,
    client,
    monkeypatch,
):
    _install_product_key(
        app,
        monkeypatch,
        username="cp19j_scope_owner",
        scopes=["ka:read"],
    )
    headers = {"X-API-Key": "ukg_phase19_read_only"}

    denied = client.post(
        "/api/v1/ka/runs/plan",
        json=_plan_body(key="cp19j-scope-denial"),
        headers=headers,
    )

    assert denied.status_code == 403
    assert denied.get_json()["code"] == "KA_SCOPE_DENIED"
    assert denied.get_json()["required_scope"] == "ka:plan"


def test_two_keys_for_the_same_owner_have_separate_run_namespaces(
    app,
    client,
    monkeypatch,
):
    owner_id, _ = _install_product_key(
        app,
        monkeypatch,
        username="cp19j_shared_owner_key_a",
        scopes=["ka:read", "ka:plan"],
    )
    body = _plan_body(key="cp19j-shared-owner")
    first = client.post(
        "/api/v1/ka/runs/plan",
        json=body,
        headers={"X-API-Key": "ukg_phase19_key_a"},
    )
    assert first.status_code == 201
    first_run_id = first.get_json()["run"]["run_id"]

    _install_product_key(
        app,
        monkeypatch,
        username="cp19j_shared_owner_key_b",
        scopes=["ka:read", "ka:plan"],
        user_id=owner_id,
    )
    hidden = client.get(
        f"/api/v1/ka/runs/{first_run_id}",
        headers={"X-API-Key": "ukg_phase19_key_b"},
    )
    assert hidden.status_code == 404
    assert client.get(
        "/api/v1/ka/runs",
        headers={"X-API-Key": "ukg_phase19_key_b"},
    ).get_json()["runs"] == []

    second = client.post(
        "/api/v1/ka/runs/plan",
        json=body,
        headers={"X-API-Key": "ukg_phase19_key_b"},
    )
    assert second.status_code == 201
    assert second.get_json()["run"]["run_id"] != first_run_id


def test_durable_runner_executes_canonical_plan_and_exposes_evidence(app):
    from models import KAProductRun

    with app.app_context():
        user_id = create_test_user(
            username="cp19j_runner_owner",
            email="cp19j_runner_owner@test.com",
        )
        request = validate_plan_request(
            _plan_body(key="cp19j-runner-evidence")
        )
        run, plan, token, replayed = plan_product_run(
            request,
            user_id=user_id,
            api_key_id=None,
            tenant_id=None,
            scopes={"ka:read", "ka:plan", "ka:execute", "ka:cancel"},
        )
        assert replayed is False
        assert plan["valid"] is True
        assert token
        confirm_and_queue_product_run(run, confirmation_token=token)
        run_id = str(run.id)

    runner = KAProductRunRunner(app, max_workers=1)
    runner._run(run_id)

    with app.app_context():
        completed = db.session.get(KAProductRun, uuid.UUID(run_id))
        assert completed.status == "succeeded"
        assert completed.result_size_bytes > 0
        result = decrypt_product_result(completed)
        assert result["schema_version"] == "dle.ka-product-result.v1"
        canonical = result["report"]["results"]["KA-004"]
        assert canonical["success"] is True
        assert canonical["output"]["normalized_query"] == (
            "Review this governed request"
        )
        trace = trace_summary(result)
        assert trace["status"] == "succeeded"
        assert "KA-004" in trace["traces"]
        assert result_artifacts(result) == []
        assert result_effects(result) == []
        with pytest.raises(
            KAProductWorkflowError,
            match="valid authoritative service receipt",
        ):
            _validate_applied_effect_receipts({
                "report": {
                    "plan_id": result["report"]["plan_id"],
                    "results": {
                        "KA-004": {
                            "effects": [{
                                "effect_id": "forged",
                                "kind": "write",
                                "status": "applied",
                                "service": "knowledge-store",
                                "idempotency_key": "forged-key",
                                "authoritative_receipt": {
                                    "schema_version": (
                                        "dle.authoritative-effect-receipt.v1"
                                    ),
                                    "status": "applied",
                                    "service": "knowledge-store",
                                    "operation": "write",
                                    "resource_id": "resource",
                                    "idempotency_key": "forged-key",
                                    "request_sha256": "not-a-sha256",
                                    "result_sha256": "also-not-a-sha256",
                                    "ka_plan_id": result["report"]["plan_id"],
                                },
                            }],
                        },
                    },
                },
            })
        completed.result_sha256 = None
        db.session.commit()
        with pytest.raises(
            KAProductWorkflowError,
            match="integrity verification",
        ):
            decrypt_product_result(completed)
        completed.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        db.session.commit()
        replacement, _plan, _token, replayed = plan_product_run(
            request,
            user_id=user_id,
            api_key_id=None,
            tenant_id=None,
            scopes={"ka:read", "ka:plan", "ka:execute", "ka:cancel"},
        )
        assert replayed is False
        assert str(replacement.id) != run_id

    runner.stop()


def test_cp19j_source_verifier_accepts_the_current_cp19k_manifest_lineage():
    evidence = verify_cp19j()

    assert evidence["status"] == "pass", evidence["errors"]


def test_durable_runner_fails_interrupted_work_without_replay(app):
    from models import KAProductRun

    with app.app_context():
        user_id = create_test_user(
            username="cp19j_interrupted_owner",
            email="cp19j_interrupted_owner@test.com",
        )
        request = validate_plan_request(
            _plan_body(key="cp19j-interrupted-run")
        )
        run, _plan, _token, _replayed = plan_product_run(
            request,
            user_id=user_id,
            api_key_id=None,
            tenant_id=None,
            scopes={"ka:read", "ka:plan", "ka:execute", "ka:cancel"},
        )
        run.status = "running"
        db.session.commit()
        run_id = run.id

    runner = KAProductRunRunner(app, max_workers=1)
    runner.start()

    with app.app_context():
        interrupted = db.session.get(KAProductRun, run_id)
        assert interrupted.status == "failed"
        assert interrupted.error_code == "KA_RUN_INTERRUPTED"
        assert interrupted.completed_at is not None

        request = validate_plan_request(
            _plan_body(key="cp19j-leased-running")
        )
        leased, _plan, _token, _replayed = plan_product_run(
            request,
            user_id=user_id,
            api_key_id=None,
            tenant_id=None,
            scopes={"ka:read", "ka:plan", "ka:execute", "ka:cancel"},
        )
        leased.status = "running"
        db.session.commit()
        leased_id = leased.id

    coordinator = MagicMock()
    coordinator.acquire.return_value = False
    runner._coordinator = coordinator
    runner._reconcile_running_once()
    with app.app_context():
        assert db.session.get(KAProductRun, leased_id).status == "running"

    coordinator.acquire.return_value = True
    coordinator.release.return_value = True
    runner._reconcile_running_once()
    with app.app_context():
        reconciled = db.session.get(KAProductRun, leased_id)
        assert reconciled.status == "failed"
        assert reconciled.error_code == "KA_RUN_INTERRUPTED"

    runner.stop()
