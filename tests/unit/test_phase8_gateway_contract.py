"""Failure-first tests for the Phase 8 external gateway foundation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.llm_gateway.external_contract import (
    GATEWAY_CONTRACT_VERSION,
    GatewayProfile,
    apply_virtual_model,
    normalize_client_scopes,
    resolve_gateway_profile,
    scope_allows,
    virtual_model_catalog,
)
from backend.llm_gateway.schemas import GatewayChatRequest


def test_gateway_profiles_are_versioned_and_private_mode_fails_closed() -> None:
    assert GATEWAY_CONTRACT_VERSION == "dle-gateway.v1"
    assert resolve_gateway_profile(None) is GatewayProfile.DESKTOP_LOOPBACK
    assert resolve_gateway_profile("same_host_gateway") is GatewayProfile.SAME_HOST_GATEWAY
    with pytest.raises(RuntimeError, match="TLS.*firewall.*qualification"):
        resolve_gateway_profile("private_windows_gateway")
    with pytest.raises(RuntimeError, match="Unsupported DataLogicEngine gateway profile"):
        resolve_gateway_profile("public_internet")


def test_client_scopes_never_treat_read_as_model_execution() -> None:
    read_only = normalize_client_scopes({"read": True})
    assert scope_allows(read_only, "run:read") is True
    assert scope_allows(read_only, "trace:read") is True
    assert scope_allows(read_only, "chat") is False

    explicit = normalize_client_scopes({"scopes": ["chat", "run:cancel"]})
    assert explicit == frozenset({"chat", "run:cancel"})
    assert scope_allows(explicit, "stream") is False

    override = normalize_client_scopes({"scopes": ["chat", "routing:override"]})
    assert scope_allows(override, "routing:override") is True


def test_virtual_models_map_to_server_owned_modes_without_provider_override() -> None:
    catalog = virtual_model_catalog()
    assert set(catalog) == {"dle-standard", "dle-enhanced", "dle-local-review"}
    assert catalog["dle-enhanced"]["mode"] == "enhanced"
    assert catalog["dle-enhanced"]["max_provider_calls"] == 2

    payload = {"virtual_model": "dle-enhanced", "mode": None, "meta": {}}
    apply_virtual_model(payload)
    assert payload["mode"] == "enhanced"
    assert payload["meta"]["virtual_model"] == "dle-enhanced"

    with pytest.raises(ValueError, match="conflicts"):
        apply_virtual_model({"virtual_model": "dle-enhanced", "mode": "standard"})


@pytest.mark.parametrize(
    ("frontend_mode", "expected_virtual_model", "expected_mode"),
    [
        ("chat", "dle-standard", "standard"),
        ("trace", "dle-standard", "standard"),
        ("explain", "dle-standard", "standard"),
        ("quad", "dle-enhanced", "enhanced"),
    ],
)
def test_virtual_models_normalize_desktop_mode_aliases(
    frontend_mode: str,
    expected_virtual_model: str,
    expected_mode: str,
) -> None:
    payload = GatewayChatRequest.model_validate({
        "messages": [{"role": "user", "content": "Desktop chat request"}],
        "request_id": "12345678-1234-1234-1234-123456789abc",
        "mode": frontend_mode,
        "run_ukg_pipeline": True,
        "meta": {"budget_warning_confirmed": False},
    }).model_dump()

    policy = apply_virtual_model(payload)

    assert policy.id == expected_virtual_model
    assert payload["virtual_model"] == expected_virtual_model
    assert payload["mode"] == expected_mode


def test_virtual_model_catalog_uses_postgresql_authority_in_app_context(app) -> None:
    from extensions import db
    from models import GatewayVirtualModel

    with app.app_context():
        db.session.add(GatewayVirtualModel(
            id='dle-standard',
            label='Database-owned Standard',
            mode='standard',
            max_provider_calls=1,
            provider_backed=True,
            description='Database authority test',
            policy={'validation': 'required'},
        ))
        db.session.commit()
        catalog = virtual_model_catalog()

    assert catalog['dle-standard']['label'] == 'Database-owned Standard'
    assert catalog['dle-standard']['policy'] == {'validation': 'required'}


def test_gateway_chat_schema_rejects_unknown_fields_and_nested_message_drift() -> None:
    with pytest.raises(ValidationError, match="extra_forbidden"):
        GatewayChatRequest.model_validate({
            "messages": [{"role": "user", "content": "hello"}],
            "silently_ignored": True,
        })

    with pytest.raises(ValidationError, match="extra_forbidden"):
        GatewayChatRequest.model_validate({
            "messages": [{"role": "user", "content": "hello", "hidden": "value"}],
        })


def test_trace_settings_is_not_public_until_it_controls_execution() -> None:
    with pytest.raises(ValidationError, match="trace_settings"):
        GatewayChatRequest.model_validate({
            "messages": [{"role": "user", "content": "hello"}],
            "trace_settings": {"enabled": False},
        })


def test_gateway_request_schema_enforces_pre_execution_size_limits() -> None:
    with pytest.raises(ValidationError, match="at most 64"):
        GatewayChatRequest.model_validate({
            "messages": [
                {"role": "user", "content": f"message-{index}"}
                for index in range(65)
            ],
        })
    with pytest.raises(ValidationError, match="200000 bytes"):
        GatewayChatRequest.model_validate({
            "messages": [{"role": "user", "content": "x" * 200_001}],
        })
    with pytest.raises(ValidationError, match="32768 bytes"):
        GatewayChatRequest.model_validate({
            "messages": [{"role": "user", "content": "hello"}],
            "meta": {"oversized": "x" * 33_000},
        })
