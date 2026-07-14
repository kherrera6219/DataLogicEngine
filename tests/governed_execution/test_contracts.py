import pytest

from backend.governed_execution.contracts import (
    GOVERNED_CONTRACT_VERSION,
    GovernedMode,
    GovernedRequest,
)
from backend.llm_gateway.gateway import GatewayRequest


def test_contract_normalizes_supported_compatibility_modes():
    request = GovernedRequest(
        messages=[{"role": "user", "content": "hello"}],
        mode="quad",
    )

    assert request.contract_version == GOVERNED_CONTRACT_VERSION
    assert request.mode is GovernedMode.ENHANCED
    assert request.query_text() == "hello"


def test_contract_rejects_unknown_version_and_missing_user_message():
    with pytest.raises(ValueError, match="Unsupported governed contract version"):
        GovernedRequest(
            messages=[{"role": "user", "content": "hello"}],
            contract_version="governed.v0",
        )
    with pytest.raises(ValueError, match="requires a user message"):
        GovernedRequest(messages=[{"role": "system", "content": "system"}])


def test_gateway_adapter_refuses_legacy_pipeline_bypass():
    request = GovernedRequest.from_gateway(
        GatewayRequest(
            messages=[{"role": "user", "content": "hello"}],
            run_ukg_pipeline=False,
            mode="chat",
        )
    )

    assert request.mode is GovernedMode.STANDARD
    assert request.metadata["compatibility_warnings"] == [
        "run_ukg_pipeline=false is deprecated and does not bypass governance"
    ]
