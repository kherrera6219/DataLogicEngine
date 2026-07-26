from __future__ import annotations

import asyncio
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

    async def _direct_llm_call(
        self, provider, model, messages, temperature, max_tokens
    ):
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


class _RefinementGateway(_Gateway):
    def __init__(self, *, refinement_ok=True, converges=True):
        super().__init__()
        self.refinement_ok = refinement_ok
        self.converges = converges

    async def _direct_llm_call(
        self, provider, model, messages, temperature, max_tokens
    ):
        self.provider_calls += 1
        self.provider_messages.append(messages)
        if self.provider_calls == 2 and not self.refinement_ok:
            return {
                "ok": False,
                "error": "refinement provider unavailable",
                "retryable": False,
            }
        answer = "Completely unrelated assertion [S1]"
        if self.provider_calls == 2 and self.converges:
            answer = "alpha evidence [S1]"
        return {
            "ok": True,
            "answer": answer,
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }


class _SlowGateway(_Gateway):
    async def _direct_llm_call(
        self, provider, model, messages, temperature, max_tokens
    ):
        self.provider_calls += 1
        await asyncio.sleep(30)
        return {"ok": True, "answer": "late answer", "usage": {}}


class _PersistenceFailureGateway(_Gateway):
    async def _create_trace_run(self, payload, *args):
        return False


class _PIIGateway(_Gateway):
    async def _direct_llm_call(
        self,
        provider,
        model,
        messages,
        temperature,
        max_tokens,
    ):
        self.provider_calls += 1
        self.provider_messages.append(messages)
        return {
            "ok": True,
            "answer": "Contact admin@example.com for support.",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }


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
    def __init__(
        self,
        *,
        normalized_query: str | None = None,
        adversarial_block: bool = False,
    ):
        self.normalized_query = normalized_query
        self.adversarial_block = adversarial_block

    async def execute(self, query, **kwargs):
        return {
            "ok": True,
            "mode": kwargs["mode"],
            "steps_executed": [
                {
                    "step": "admission_and_routing",
                    "ka_id": "KA-004",
                    "status": "completed",
                    "input": {"query": query},
                    "output": {
                        "is_valid": True,
                        "normalized_query": self.normalized_query or query,
                    },
                    "duration_ms": 2,
                },
                {
                    "step": "admission_and_routing",
                    "ka_id": "KA-061",
                    "status": "completed",
                    "input": {"query": query},
                    "output": {
                        "blocked": self.adversarial_block,
                        "veto": self.adversarial_block,
                        "sanitized_query": self.normalized_query or query,
                    },
                    "duration_ms": 2,
                },
                {
                    "step": "candidate_preparation",
                    "ka_id": "KA-001",
                    "status": "completed",
                    "input": {"query": query},
                    "output": {"strategy": "simple"},
                    "duration_ms": 2,
                },
            ],
        }


def _orchestrator(
    gateway: _Gateway,
    *,
    dmrf_ok: bool = True,
    truthcore: _TruthCore | None = None,
):
    return GovernedExecutionOrchestrator(
        gateway,
        dmrf_factory=lambda **kwargs: _DMRF(ok=dmrf_ok),
        dsqp_factory=lambda **kwargs: _DSQP(),
        truthcore=truthcore or _TruthCore(),
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
            [
                EvidenceRecord(
                    source_id="source-alpha", citation_label="S1", text="alpha evidence"
                )
            ],
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
    assert '"ka_id": "KA-001"' in system
    assert [stage.name for stage in result.stages] == [
        "admission",
        "dmrf_routing",
        "layer_1_normalize_route",
        "layer_2_retrieve_context",
        "layer_3_evidence_plan",
        "layer_4_persona_context",
        "layer_5_candidate_plan",
        "provider_execution",
        "layer_6_evidence_validation",
        "layer_7_reasoning_boundary",
        "layer_8_trust_policy_gate",
        "layer_9_convergence",
        "layer_10_release_gate",
        "persistence",
    ]
    assert all(stage.status.value == "completed" for stage in result.stages)
    assert [item["stage_id"] for item in gateway.persisted[0]["trace"]] == [
        stage.stage_id for stage in result.stages
    ]
    reasoning = result.metadata["reasoning_state"]
    assert [layer["layer_id"] for layer in reasoning["layers"]] == [
        f"L{index}" for index in range(1, 11)
    ]
    assert reasoning["release"]["decision"] == "release"
    layers = {layer["layer_id"]: layer for layer in reasoning["layers"]}
    expected_l9 = {f"L9-KA-{number:03d}" for number in range(1, 8)}
    expected_l10 = {f"L10-KA-{number:03d}" for number in range(1, 8)}
    assert set(layers["L9"]["selected_ka_ids"]) == expected_l9
    assert set(layers["L9"]["ka_results"]) == expected_l9
    assert set(layers["L9"]["outputs"]["kas_invoked"]) == expected_l9
    assert set(layers["L10"]["selected_ka_ids"]) == expected_l10
    assert set(layers["L10"]["ka_results"]) == expected_l10
    assert set(layers["L10"]["outputs"]["kas_invoked"]) == expected_l10
    assert layers["L10"]["outputs"]["effects_applied"] is False
    assert reasoning["effects"] == [
        {
            "ka_id": "KA-012",
            "state": "proposal_only",
            "effect_port": "persona_context_service",
            "applied": False,
            "receipt": None,
        }
    ]
    ka = result.metadata["truthcore"]["steps_executed"][0]
    assert ka["input"] == {"query": "Assess the evidence"}
    assert ka["output"]["normalized_query"] == "Assess the evidence"
    assert ka["duration_ms"] == 2


@pytest.mark.asyncio
async def test_l10_redacts_pii_without_returning_sensitive_trace_data(
    monkeypatch,
):
    import json

    import backend.governed_execution.orchestrator as module

    monkeypatch.setattr(
        module,
        "retrieve_evidence",
        lambda *args, **kwargs: ([], []),
    )
    result = await _orchestrator(_PIIGateway()).execute(
        _request(mode=GovernedMode.STANDARD)
    )

    assert result.ok is True
    assert result.answer == "Contact [REDACTED_EMAIL] for support."
    payload = json.dumps(result.to_dict(), default=str)
    assert "admin@example.com" not in payload
    l10 = result.metadata["reasoning_state"]["layers"][-1]
    assert l10["outputs"]["privacy"] == {
        "redactions_found": 1,
        "sensitive_values_returned": False,
    }


@pytest.mark.asyncio
async def test_l9_blocks_forged_uncommitted_ka_trace(monkeypatch):
    import backend.governed_execution.orchestrator as module

    monkeypatch.setattr(
        module,
        "retrieve_evidence",
        lambda *args, **kwargs: (
            [
                EvidenceRecord(
                    source_id="source-alpha",
                    citation_label="S1",
                    text="alpha evidence",
                )
            ],
            [],
        ),
    )
    orchestrator = _orchestrator(_Gateway())
    original_trace = orchestrator.layer_stages._committed_layer_trace

    def forged_trace(context, *, through_layer):
        trace = original_trace(context, through_layer=through_layer)
        trace["layer8"]["selected_ka_ids"] = ["KA-FORGED"]
        trace["layer8"]["ka_results"] = {}
        return trace

    monkeypatch.setattr(
        orchestrator.layer_stages,
        "_committed_layer_trace",
        forged_trace,
    )
    result = await orchestrator.execute(_request())

    assert result.ok is False
    assert result.status == "policy_block"
    assert result.failure.code == "L9_CONVERGENCE_BLOCK"
    assert (
        result.metadata["reasoning_state"]["convergence"]["reason"]
        == "l9_trace_forgery_detected"
    )


@pytest.mark.asyncio
async def test_l10_required_suite_exception_blocks_release(monkeypatch):
    import backend.governed_execution.orchestrator as module

    monkeypatch.setattr(
        module,
        "retrieve_evidence",
        lambda *args, **kwargs: (
            [
                EvidenceRecord(
                    source_id="source-alpha",
                    citation_label="S1",
                    text="alpha evidence",
                )
            ],
            [],
        ),
    )
    orchestrator = _orchestrator(_Gateway())
    original_execute = orchestrator.layer_stages.ka_executor.execute

    async def fail_l10(plan, request):
        if any(ka_id.startswith("L10-") for ka_id in plan.selected_ids):
            raise TimeoutError("injected required L10 timeout")
        return await original_execute(plan, request)

    monkeypatch.setattr(
        orchestrator.layer_stages.ka_executor,
        "execute",
        fail_l10,
    )
    result = await orchestrator.execute(_request())

    assert result.ok is False
    assert result.status == "policy_block"
    assert result.failure.code == "L10_REQUIRED_KA_FAILURE"
    assert result.metadata["reasoning_state"]["release"] == {
        "decision": "halt",
        "final_action": "finalize",
        "reason": "required_l10_plan_failed",
        "error_type": "TimeoutError",
    }


@pytest.mark.asyncio
async def test_selected_l1_ka_output_changes_query_consumed_by_provider(monkeypatch):
    import backend.governed_execution.orchestrator as module

    monkeypatch.setattr(
        module,
        "retrieve_evidence",
        lambda *args, **kwargs: (
            [
                EvidenceRecord(
                    source_id="source-alpha",
                    citation_label="S1",
                    text="alpha evidence",
                )
            ],
            [],
        ),
    )
    gateway = _Gateway()
    result = await _orchestrator(
        gateway,
        truthcore=_TruthCore(normalized_query="Normalized governed query"),
    ).execute(_request())

    assert result.ok is True
    assert gateway.provider_messages[0][-1]["content"] == "Normalized governed query"
    assert (
        result.metadata["reasoning_state"]["layers"][0]["outputs"]["query"]
        == "Normalized governed query"
    )


@pytest.mark.asyncio
async def test_selected_l1_adversarial_result_blocks_before_retrieval_and_provider(
    monkeypatch,
):
    import backend.governed_execution.orchestrator as module

    retrieval_called = False

    def retrieve(*args, **kwargs):
        nonlocal retrieval_called
        retrieval_called = True
        return [], []

    monkeypatch.setattr(module, "retrieve_evidence", retrieve)
    gateway = _Gateway()
    result = await _orchestrator(
        gateway,
        truthcore=_TruthCore(adversarial_block=True),
    ).execute(_request())

    assert result.ok is False
    assert result.failure.code == "L1_INPUT_BLOCKED"
    assert retrieval_called is False
    assert gateway.provider_calls == 0
    l1 = result.metadata["reasoning_state"]["layers"][0]
    assert l1["selected_ka_ids"] == ["KA-004", "KA-061", "KA-001"]
    assert l1["status"] == "blocked"


@pytest.mark.asyncio
async def test_l10_release_is_required_before_success_persistence(monkeypatch):
    import backend.governed_execution.orchestrator as module
    from backend.governed_execution.ten_layers import LayerExecution

    monkeypatch.setattr(
        module,
        "retrieve_evidence",
        lambda *args, **kwargs: (
            [
                EvidenceRecord(
                    source_id="source-alpha",
                    citation_label="S1",
                    text="alpha evidence",
                )
            ],
            [],
        ),
    )
    gateway = _Gateway()
    orchestrator = _orchestrator(gateway)
    monkeypatch.setattr(
        orchestrator.layer_stages,
        "l10",
        lambda *args, **kwargs: LayerExecution(
            ok=False,
            outputs={
                "layer_id": "L10",
                "release": {"decision": "halt"},
            },
            error_code="L10_TEST_HALT",
        ),
    )

    result = await orchestrator.execute(_request())

    assert result.ok is False
    assert result.answer == ""
    assert result.failure.code == "L10_TEST_HALT"
    assert gateway.provider_calls == 1
    assert gateway.persisted[-1]["failure"]["code"] == "L10_TEST_HALT"
    assert gateway.persisted[-1]["metadata"]["reasoning_state"]["release"] is None


@pytest.mark.asyncio
async def test_changing_retrieved_evidence_changes_final_result(monkeypatch):
    import backend.governed_execution.orchestrator as module

    current = {"text": "alpha evidence"}

    def retrieve(*args, **kwargs):
        return [
            EvidenceRecord(
                source_id="source-1", citation_label="S1", text=current["text"]
            )
        ], []

    monkeypatch.setattr(module, "retrieve_evidence", retrieve)
    first = await _orchestrator(_Gateway()).execute(_request())
    current["text"] = "beta evidence"
    second = await _orchestrator(_Gateway()).execute(_request())

    assert first.answer != second.answer
    assert first.claims[0].evidence_ids == [first.evidence[0].evidence_id]
    assert second.claims[0].evidence_ids == [second.evidence[0].evidence_id]
    assert first.evidence[0].source_id == "source-1"
    assert second.evidence[0].source_id == "source-1"
    assert first.evidence[0].evidence_id != second.evidence[0].evidence_id


@pytest.mark.asyncio
async def test_truth_gate_block_prevents_provider_call_and_persists_failure(
    monkeypatch,
):
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
    assert "layer_6_evidence_validation" not in names
    assert result.stages[names.index("provider_execution")].status.value == "failed"


@pytest.mark.asyncio
async def test_enhanced_refinement_converges_once_and_terminates(monkeypatch):
    import backend.governed_execution.orchestrator as module

    monkeypatch.setattr(
        module,
        "retrieve_evidence",
        lambda *args, **kwargs: (
            [
                EvidenceRecord(
                    source_id="source-alpha", citation_label="S1", text="alpha evidence"
                )
            ],
            [],
        ),
    )
    gateway = _RefinementGateway()
    result = await _orchestrator(gateway).execute(_request())

    assert result.status == "completed"
    assert result.convergence.action == "finalize"
    assert gateway.provider_calls == 2
    assert [stage.name for stage in result.stages].count("refinement_1") == 1
    post_candidate = [
        (layer["layer_id"], layer["iteration"])
        for layer in result.metadata["reasoning_state"]["layers"]
        if layer["layer_id"] in {"L6", "L7", "L8", "L9"}
    ]
    assert post_candidate == [
        ("L6", 0),
        ("L7", 0),
        ("L8", 0),
        ("L9", 0),
        ("L6", 1),
        ("L7", 1),
        ("L8", 1),
        ("L9", 1),
    ]


@pytest.mark.asyncio
async def test_repeated_nonconvergence_blocks_at_recursion_limit(monkeypatch):
    import backend.governed_execution.orchestrator as module

    monkeypatch.setattr(
        module,
        "retrieve_evidence",
        lambda *args, **kwargs: (
            [
                EvidenceRecord(
                    source_id="source-alpha", citation_label="S1", text="alpha evidence"
                )
            ],
            [],
        ),
    )
    gateway = _RefinementGateway(converges=False)
    result = await _orchestrator(gateway).execute(_request())

    assert result.status == "policy_block"
    assert result.failure.code == "L9_CONVERGENCE_BLOCK"
    assert result.metadata["reasoning_state"]["convergence"]["action"] == "block"
    assert (
        result.metadata["reasoning_state"]["convergence"]["reason"]
        == "l9_recursion_budget_exhausted"
    )
    assert gateway.provider_calls == 2


@pytest.mark.asyncio
async def test_refinement_provider_failure_is_terminal(monkeypatch):
    import backend.governed_execution.orchestrator as module

    monkeypatch.setattr(
        module,
        "retrieve_evidence",
        lambda *args, **kwargs: (
            [
                EvidenceRecord(
                    source_id="source-alpha", citation_label="S1", text="alpha evidence"
                )
            ],
            [],
        ),
    )
    gateway = _RefinementGateway(refinement_ok=False)
    result = await _orchestrator(gateway).execute(_request())

    assert result.ok is False
    assert result.failure.code == "PROVIDER_REFINEMENT_FAILURE"
    assert gateway.provider_calls == 2


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
async def test_simulation_redirects_to_durable_job_contract(monkeypatch):
    import backend.governed_execution.orchestrator as module

    def unexpected_retrieval(*args, **kwargs):
        raise AssertionError("simulation boundary must precede retrieval")

    monkeypatch.setattr(module, "retrieve_evidence", unexpected_retrieval)
    gateway = _Gateway()
    result = await _orchestrator(gateway).execute(
        _request(mode=GovernedMode.SIMULATION)
    )

    assert result.failure.kind is GovernedFailureKind.VALIDATION_FAILURE
    assert result.failure.code == "SIMULATION_DURABLE_JOB_REQUIRED"
    assert result.failure.stage == "simulation_job_contract"
    assert gateway.provider_calls == 0
    assert [stage.name for stage in result.stages] == [
        "admission",
        "simulation_job_contract",
        "persistence",
    ]
    assert result.stages[1].status.value == "failed"


@pytest.mark.asyncio
async def test_active_request_cancellation_stops_provider_and_finalizes_trace(
    monkeypatch,
):
    import backend.governed_execution.orchestrator as module
    from backend.governed_execution.cancellation import CANCELLATION_REGISTRY

    monkeypatch.setattr(module, "retrieve_evidence", lambda *args, **kwargs: ([], []))
    gateway = _SlowGateway()
    request = _request(mode=GovernedMode.STANDARD, request_id="cancel-request-123")
    task = asyncio.create_task(_orchestrator(gateway).execute(request))
    for _ in range(200):
        if gateway.provider_calls:
            break
        await asyncio.sleep(0.005)

    assert CANCELLATION_REGISTRY.cancel(request.request_id) is True
    result = await asyncio.wait_for(task, timeout=2)

    assert result.failure.kind is GovernedFailureKind.CANCELLED
    assert result.failure.code == "REQUEST_CANCELLED"
    assert gateway.provider_calls == 1
    assert gateway.persisted[-1]["failure"]["kind"] == "cancelled"


@pytest.mark.asyncio
async def test_request_wide_deadline_cancels_slow_provider_and_finalizes(monkeypatch):
    import backend.governed_execution.orchestrator as module

    monkeypatch.setattr(module, "retrieve_evidence", lambda *args, **kwargs: ([], []))
    monkeypatch.setenv("GOVERNED_REQUEST_DEADLINE_SECONDS", "1")
    gateway = _SlowGateway()
    result = await _orchestrator(gateway).execute(
        _request(mode=GovernedMode.STANDARD, constraints={"deadline_seconds": 1})
    )

    assert result.failure.kind is GovernedFailureKind.TIMEOUT
    assert result.failure.code == "REQUEST_DEADLINE_EXCEEDED"
    assert gateway.persisted[-1]["failure"]["kind"] == "timeout"


@pytest.mark.asyncio
async def test_provider_success_is_not_released_when_trace_persistence_fails(
    monkeypatch,
):
    import backend.governed_execution.orchestrator as module

    monkeypatch.setattr(
        module,
        "retrieve_evidence",
        lambda *args, **kwargs: (
            [
                EvidenceRecord(
                    source_id="source-alpha", citation_label="S1", text="alpha evidence"
                )
            ],
            [],
        ),
    )
    result = await _orchestrator(_PersistenceFailureGateway()).execute(
        _request(mode=GovernedMode.STANDARD)
    )

    assert result.ok is False
    assert result.answer == ""
    assert result.failure.code == "TRACE_PERSISTENCE_FAILURE"
    assert result.failure.details["provider_succeeded"] is True
