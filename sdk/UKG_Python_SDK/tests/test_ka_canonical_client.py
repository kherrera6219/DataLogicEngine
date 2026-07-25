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
