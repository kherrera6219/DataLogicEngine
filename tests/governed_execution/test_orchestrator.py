from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from backend.governed_execution.contracts import (
    EvidenceRecord,
    GovernedFailureKind,
    GovernedMode,
    GovernedRequest,
)
from backend.governed_execution.orchestrator import GovernedExecutionOrchestrator


class _Governance:
    def prepare_request(self, request: Any, query: str):
        return SimpleNamespace(
            ok=True,
            query=query.strip(),
            error=None,
            governance_flags=["admitted"],
            estimated_request_tokens=4,
            prompt_template_key=None,
            prompt_template_version=None,
            routing_policy_name=None,
            routing_policy_version=None,
            allowed_provider_types=set(),
            allowed_models=set(),
        )

    def record_audit_event(self, **kwargs):
        return None

    def estimate_cost_usd(self, model: str, tokens_in: int, tokens_out: int) -> float:
        return 0.001

    def apply_output_controls(self, answer: str):
        return answer, "public", []


class _Circuit:
    def can_execute(self):
        return True

    def record_success(self):
        return None

    def record_failure(self):
        return None


class _Gateway:
    def __init__(self, *, provider_ok: bool = True):
        self._governance = _Governance()
        self.provider_ok = provider_ok
        self.provider_calls = 0
        self.provider_messages: list[list[dict[str, Any]]] = []
        self.persisted: list[dict[str, Any]] = []
        self.db = None

    @staticmethod
    def _desktop_local_first_enabled():
        return True

    @staticmethod
    def _normalize_allowlist(values):
        return {str(item).lower() for item in values or []}

    @staticmethod
    def _preferred_env_provider():
        return None

    async def _get_eligible_providers(self, *args, **kwargs):
        return [
            SimpleNamespace(
                id="provider-1",
                name="Test Provider",
                provider_type="openai",
                model_id="test-model",
                api_version="test",
            )
        ]

    @staticmethod
    def _get_circuit_breaker(provider_id):
        return _Circuit()

    @staticmethod
    def _resolve_model(request, provider):
        return request.model or provider.model_id

    @staticmethod
    def _provider_timeout_seconds(provider):
        return 5

    @staticmethod
    def _provider_max_retries(provider):
        return 1

    @staticmethod
    def _create_sdk_provider(provider):
        return provider

    async def _direct_llm_call(self, provider, model, messages, temperature, max_tokens):
        self.provider_calls += 1
        self.provider_messages.append(messages)
        if not self.provider_ok:
            return {"ok": False, "error": "provider unavailable", "retryable": False}
        system = str(messages[0]["content"])
        marker = "alpha" if "alpha evidence" in system else "beta"
        return {
            "ok": True,
            "answer": f"Answer from {marker} evidence [S1]",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

    async def _record_usage(self, *args, **kwargs):
        return None

    async def _save_chat_message(self, *args, **kwargs):
        return None

    async def _create_trace_run(self, payload, *args):
        self.persisted.append(payload)
        return True

    @staticmethod
    def _public_error_message(error):
        return str(error or "provider failed")

    @staticmethod
    def _is_rate_limit_error(error):
        return False

    @staticmethod
    def _is_retryable_error(error):
        return False

    @staticmethod
    async def _retry_backoff_sleep(attempt):
        return None


class _DMRFResult:
    def __init__(self, *, ok: bool = True):
        self.ok = ok
        self.tier = "moderate"
        self.warnings = [] if ok else ["blocked fixture"]
        self.gate_result = {"decision": "allow" if ok else "block"}

    def export_bundle(self):
        return {
            "run_id": "dmrf-fixture",
            "tier": self.tier,
            "warnings": self.warnings,
            "gate_result": self.gate_result,
            "axis_vector": {
                "confidence": 1.0,
                "axes": {
                    "15": {"value": "standard"},
                    "17": {"value": "default"},
                },
            },
            "steps": [{"name": "truth_gate", "status": "completed"}],
        }


class _DMRF:
    def __init__(self, *, ok: bool = True):
        self.ok = ok

    async def process(self, *args, **kwargs):
        return _DMRFResult(ok=self.ok)


class _DSQP:
    async def construct_all(self, *args, **kwargs):
        return {
            "profiles": {
                str(axis): {
                    "persona_id": f"persona-{axis}",
                    "axis_number": axis,
                    "persona_type": name,
                    "name": f"{name.title()} expert",
                    "description": f"{name} contribution",
                    "components": {"skills": {"items": ["analysis"]}},
                    "metadata": {"construction_mode": "deterministic"},
                    "validation": {"valid": True, "errors": []},
                }
                for axis, name in (
                    (8, "knowledge"),
                    (9, "sector"),
                    (10, "regulatory"),
                    (11, "compliance"),
                )
            },
            "failures": {},
            "partial": False,
        }


class _TruthCore:
    async def execute(self, query, **kwargs):
        return {
            "ok": True,
            "mode": kwargs["mode"],
            "steps_executed": [
                {
                    "step": "complexity_routing",
                    "ka_id": "KA-113",
                    "status": "completed",
                    "input": {"query": query},
                    "output": {"route": "standard"},
                    "duration_ms": 2,
                }
            ],
        }


def _orchestrator(gateway: _Gateway, *, dmrf_ok: bool = True):
    return GovernedExecutionOrchestrator(
        gateway,
        dmrf_factory=lambda **kwargs: _DMRF(ok=dmrf_ok),
        dsqp_factory=lambda **kwargs: _DSQP(),
        truthcore=_TruthCore(),
    )


def _request(**kwargs):
    mode = kwargs.pop("mode", GovernedMode.ENHANCED)
    return GovernedRequest(
        messages=[{"role": "user", "content": "Assess the evidence"}],
        mode=mode,
        source="test",
        **kwargs,
    )


@pytest.mark.asyncio
async def test_evidence_dsqp_and_ka_are_causal_and_trace_matches_execution(monkeypatch):
    import backend.governed_execution.orchestrator as module

    monkeypatch.setattr(
        module,
        "retrieve_evidence",
        lambda *args, **kwargs: (
            [EvidenceRecord(source_id="source-alpha", citation_label="S1", text="alpha evidence")],
            [],
        ),
    )
    gateway = _Gateway()
    result = await _orchestrator(gateway).execute(_request())

    assert result.ok is True
    assert result.answer == "Answer from alpha evidence [S1]"
    system = gateway.provider_messages[0][0]["content"]
    assert "source_id=source-alpha" in system
    assert "knowledge contribution" in system
    assert '"ka_id": "KA-113"' in system
    assert [stage.name for stage in result.stages] == [
        "admission",
        "dmrf_routing",
        "retrieval",
        "dsqp_personas",
        "truthcore_preflight",
        "provider_request_construction",
        "provider_execution",
        "output_validation",
        "persistence",
    ]
    assert all(stage.status.value == "completed" for stage in result.stages)
    assert [item["stage_id"] for item in gateway.persisted[0]["trace"]] == [
        stage.stage_id for stage in result.stages
    ]
    ka = result.metadata["truthcore"]["steps_executed"][0]
    assert ka["input"] == {"query": "Assess the evidence"}
    assert ka["output"] == {"route": "standard"}
    assert ka["duration_ms"] == 2


@pytest.mark.asyncio
async def test_changing_retrieved_evidence_changes_final_result(monkeypatch):
    import backend.governed_execution.orchestrator as module

    current = {"text": "alpha evidence"}

    def retrieve(*args, **kwargs):
        return [EvidenceRecord(source_id="source-1", citation_label="S1", text=current["text"])], []

    monkeypatch.setattr(module, "retrieve_evidence", retrieve)
    first = await _orchestrator(_Gateway()).execute(_request())
    current["text"] = "beta evidence"
    second = await _orchestrator(_Gateway()).execute(_request())

    assert first.answer != second.answer
    assert first.claims[0].evidence_ids == ["source-1"]
    assert second.claims[0].evidence_ids == ["source-1"]


@pytest.mark.asyncio
async def test_truth_gate_block_prevents_provider_call_and_persists_failure(monkeypatch):
    import backend.governed_execution.orchestrator as module

    monkeypatch.setattr(module, "retrieve_evidence", lambda *args, **kwargs: ([], []))
    gateway = _Gateway()
    result = await _orchestrator(gateway, dmrf_ok=False).execute(_request())

    assert result.ok is False
    assert result.failure.kind is GovernedFailureKind.POLICY_BLOCK
    assert result.failure.code == "TRUTH_GATE_BLOCK"
    assert gateway.provider_calls == 0
    assert "provider_execution" not in [stage.name for stage in result.stages]
    assert gateway.persisted[0]["failure"]["kind"] == "policy_block"


@pytest.mark.asyncio
async def test_provider_failure_has_no_validation_stage(monkeypatch):
    import backend.governed_execution.orchestrator as module

    monkeypatch.setattr(module, "retrieve_evidence", lambda *args, **kwargs: ([], []))
    gateway = _Gateway(provider_ok=False)
    result = await _orchestrator(gateway).execute(_request())

    assert result.failure.kind is GovernedFailureKind.PROVIDER_FAILURE
    assert gateway.provider_calls == 1
    names = [stage.name for stage in result.stages]
    assert "output_validation" not in names
    assert result.stages[names.index("provider_execution")].status.value == "failed"


@pytest.mark.asyncio
async def test_cancellation_stops_before_routing_and_provider(monkeypatch):
    import backend.governed_execution.orchestrator as module

    monkeypatch.setattr(module, "retrieve_evidence", lambda *args, **kwargs: ([], []))
    gateway = _Gateway()
    result = await _orchestrator(gateway).execute(
        _request(metadata={"cancel_requested": True})
    )

    assert result.failure.kind is GovernedFailureKind.CANCELLED
    assert gateway.provider_calls == 0
    assert [stage.name for stage in result.stages] == ["admission", "persistence"]


@pytest.mark.asyncio
async def test_simulation_stops_at_recorded_phase10_boundary(monkeypatch):
    import backend.governed_execution.orchestrator as module

    def unexpected_retrieval(*args, **kwargs):
        raise AssertionError("simulation boundary must precede retrieval")

    monkeypatch.setattr(module, "retrieve_evidence", unexpected_retrieval)
    gateway = _Gateway()
    result = await _orchestrator(gateway).execute(
        _request(mode=GovernedMode.SIMULATION)
    )

    assert result.failure.kind is GovernedFailureKind.CAPABILITY_UNAVAILABLE
    assert result.failure.code == "SIMULATION_PHASE10_BOUNDARY"
    assert result.failure.stage == "simulation_boundary"
    assert gateway.provider_calls == 0
    assert [stage.name for stage in result.stages] == [
        "admission",
        "simulation_boundary",
        "persistence",
    ]
    assert result.stages[1].status.value == "failed"
