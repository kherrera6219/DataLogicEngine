from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from ukg_sdk.ka.executor import AsyncKAExecutor, KAExecutor
from ukg_sdk.ka.registry import load_default_registry
from ukg_sdk.utils import package_data_path


def test_generated_sdk_manifest_contains_the_deduplicated_authority():
    registry = load_default_registry(package_data_path(""))

    assert registry is not None
    assert len(registry.items) == 213
    assert registry.has("KA-1101")
    assert not registry.has("KA-133")
    assert "generated-v1:KA-133" in registry.get("KA-1101").aliases


def test_sdk_ka_executor_calls_the_installed_service():
    transport = MagicMock()
    transport.post.return_value = {
        "success": True,
        "result": {
            "algorithm_id": "KA-004",
            "output": {"is_valid": True},
            "execution_time_ms": 4,
            "trace_id": "trace-1",
            "canonical_result": {
                "schema_version": "dle.ka-execution-result.v1"
            },
        },
    }
    executor = KAExecutor(transport)

    result = executor.execute(
        "KA-004",
        {"query": "validate"},
        meta={"run_id": "run-1"},
    )

    assert result.ok is True
    assert result.output == {"is_valid": True}
    assert result.trace_id == "trace-1"
    transport.post.assert_called_once_with(
        "ka/algorithms/KA-004/execute",
        json={
            "input": {"query": "validate"},
            "context": {"run_id": "run-1"},
        },
    )


def test_sdk_rejects_private_handlers_and_run_all():
    transport = MagicMock()
    executor = KAExecutor(transport)

    with pytest.raises(TypeError, match="Client-side KA handlers"):
        executor.register("KA-001", lambda _request: {})
    with pytest.raises(TypeError, match="Run-all is forbidden"):
        executor.run_all({"query": "do everything"})
    with pytest.raises(TypeError, match="authenticated UKGClient"):
        KAExecutor()


def test_sdk_exposes_durable_plan_and_evidence_workflow():
    transport = MagicMock()
    transport.post.side_effect = [
        {
            "success": True,
            "run": {"run_id": "run-19j", "status": "planned"},
            "plan": {"plan_id": "plan-19j", "valid": True},
            "confirmation_token": "confirm-19j",
        },
        {"success": True, "run": {"run_id": "run-19j", "status": "queued"}},
        {"success": True, "run": {"run_id": "run-19j", "status": "cancelled"}},
    ]
    transport.get.side_effect = [
        {"runs": [{"run_id": "run-19j"}]},
        {"run": {"run_id": "run-19j", "status": "succeeded"}},
        {"run_id": "run-19j", "report": {}},
        {"trace": {"run_id": "run-19j"}},
        {"artifacts": []},
        {"effects": []},
    ]
    executor = KAExecutor(transport)

    planned = executor.plan(
        "KA-004",
        {"query": "validate"},
        idempotency_key="cp19j-sdk-plan",
        metadata={"source": "python-sdk"},
    )
    queued = executor.execute_plan(
        "run-19j",
        confirmation_token=planned.confirmation_token,
    )

    assert planned.run["status"] == "planned"
    assert planned.plan["plan_id"] == "plan-19j"
    assert queued["run"]["status"] == "queued"
    assert executor.runs(limit=999)["runs"][0]["run_id"] == "run-19j"
    assert executor.run("run-19j")["run"]["status"] == "succeeded"
    assert executor.result("run-19j")["run_id"] == "run-19j"
    assert executor.trace("run-19j")["trace"]["run_id"] == "run-19j"
    assert executor.artifacts("run-19j")["artifacts"] == []
    assert executor.effects("run-19j")["effects"] == []
    assert executor.cancel("run-19j")["run"]["status"] == "cancelled"
    assert transport.post.call_args_list[0].kwargs["json"] == {
        "ka_id": "KA-004",
        "input": {"query": "validate"},
        "mode": "production",
        "idempotency_key": "cp19j-sdk-plan",
        "metadata": {"source": "python-sdk"},
        "budget": {},
    }
    transport.get.assert_any_call("ka/runs", params={"limit": 200})


@pytest.mark.asyncio
async def test_async_sdk_ka_executor_calls_the_installed_service():
    transport = MagicMock()
    transport.get.return_value = {"algorithms": [{"id": "KA-004"}]}

    async def post(_path, *, json):
        assert json == {"input": {"query": "validate"}}
        return {
            "success": True,
            "result": {
                "algorithm_id": "KA-004",
                "output": {"is_valid": True},
                "execution_time_ms": 4,
            },
        }

    transport.post = post
    executor = AsyncKAExecutor(transport)

    result = await executor.execute("KA-004", {"query": "validate"})

    assert result.ok is True
    assert result.output == {"is_valid": True}


@pytest.mark.asyncio
async def test_async_sdk_exposes_durable_plan_and_cancel_workflow():
    transport = MagicMock()

    async def post(path, *, json):
        if path == "ka/runs/plan":
            assert json["idempotency_key"] == "cp19j-async-plan"
            return {
                "run": {"run_id": "run-async", "status": "planned"},
                "plan": {"plan_id": "plan-async", "valid": True},
                "confirmation_token": None,
            }
        assert path == "ka/runs/run-async/cancel"
        assert json == {}
        return {"run": {"run_id": "run-async", "status": "cancelled"}}

    transport.post = post
    executor = AsyncKAExecutor(transport)

    planned = await executor.plan(
        "KA-001",
        {"query": "review"},
        idempotency_key="cp19j-async-plan",
    )
    cancelled = await executor.cancel("run-async")

    assert planned.plan["valid"] is True
    assert cancelled["run"]["status"] == "cancelled"
