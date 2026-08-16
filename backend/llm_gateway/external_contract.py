"""Versioned Phase 8 gateway profiles, scopes, and virtual-model policy."""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from backend.product_version import CONTRACT_VERSIONS

GATEWAY_CONTRACT_VERSION = CONTRACT_VERSIONS["gateway"]
VIRTUAL_MODEL_MANIFEST_VERSION = CONTRACT_VERSIONS["virtual_model_manifest"]


class GatewayProfile(str, Enum):
    """Supported product profiles; private mode remains qualification-gated."""

    DESKTOP_LOOPBACK = "desktop_loopback"
    SAME_HOST_GATEWAY = "same_host_gateway"
    PRIVATE_WINDOWS_GATEWAY = "private_windows_gateway"


CLIENT_SCOPES = frozenset({
    "chat",
    "stream",
    "run:create",
    "run:read",
    "run:cancel",
    "trace:read",
    "evidence:read",
    "models:read",
    "routing:override",
    "ka:read",
    "ka:plan",
    "ka:execute",
    "ka:cancel",
})

ADMINISTRATIVE_SCOPES = frozenset({
    "gateway:admin",
    "provider:admin",
    "storage:admin",
    "policy:admin",
})


@dataclass(frozen=True, slots=True)
class VirtualModelPolicy:
    id: str
    label: str
    mode: str
    max_provider_calls: int
    provider_backed: bool
    description: str
    policy: dict[str, Any]


_VIRTUAL_MODELS = (
    VirtualModelPolicy(
        id="dle-standard",
        label="DataLogicEngine Standard",
        mode="standard",
        max_provider_calls=1,
        provider_backed=True,
        description="One governed answer-model call with standard validation.",
        policy={
            "provider_selection": "owner_default",
            "model_selection": "owner_default",
            "retrieval": "bounded",
            "validation": "required",
            "tools": "policy_controlled",
        },
    ),
    VirtualModelPolicy(
        id="dle-enhanced",
        label="DataLogicEngine Enhanced",
        mode="enhanced",
        max_provider_calls=2,
        provider_backed=True,
        description="One answer call plus at most one governed refinement call.",
        policy={
            "provider_selection": "owner_default",
            "model_selection": "owner_default",
            "retrieval": "bounded",
            "validation": "required",
            "tools": "policy_controlled",
        },
    ),
    VirtualModelPolicy(
        id="dle-local-review",
        label="DataLogicEngine Local Review",
        mode="local_review",
        max_provider_calls=0,
        provider_backed=False,
        description="Deterministic local evidence review without a provider answer.",
        policy={
            "provider_selection": "none",
            "model_selection": "none",
            "retrieval": "bounded",
            "validation": "required",
            "tools": "disabled",
        },
    ),
)


def _effective_virtual_models() -> tuple[VirtualModelPolicy, ...]:
    """Read migrated PostgreSQL policy in app contexts; retain pure-code test bootstrap."""
    try:
        from flask import current_app, has_app_context

        if has_app_context():
            from models import GatewayVirtualModel

            rows = GatewayVirtualModel.query.filter_by(is_active=True).order_by(
                GatewayVirtualModel.id.asc()
            ).all()
            if isinstance(rows, list) and rows:
                return tuple(VirtualModelPolicy(
                    id=row.id,
                    label=row.label,
                    mode=row.mode,
                    max_provider_calls=int(row.max_provider_calls),
                    provider_backed=bool(row.provider_backed),
                    description=row.description,
                    policy=dict(row.policy or {}),
                ) for row in rows)
            if current_app.config.get("DLE_PRODUCTION_MODE"):
                raise RuntimeError("gateway_virtual_model_authority_unavailable")
    except RuntimeError:
        raise
    except Exception as exc:
        # Model metadata and CLI tooling can import this module before the app
        # migration boundary exists. Production request handling never falls back.
        try:
            from flask import current_app, has_app_context

            if has_app_context() and current_app.config.get("DLE_PRODUCTION_MODE"):
                raise RuntimeError(
                    "gateway_virtual_model_authority_unavailable"
                ) from exc
        except RuntimeError:
            raise
    return _VIRTUAL_MODELS


def resolve_gateway_profile(raw_profile: str | None = None) -> GatewayProfile:
    """Resolve a supported profile and keep private exposure fail-closed."""

    requested = str(
        raw_profile
        or os.environ.get("DLE_GATEWAY_PROFILE")
        or GatewayProfile.DESKTOP_LOOPBACK.value
    ).strip().lower()
    try:
        profile = GatewayProfile(requested)
    except ValueError as exc:
        raise RuntimeError(
            f"Unsupported DataLogicEngine gateway profile: {requested or '<empty>'}"
        ) from exc
    if profile is GatewayProfile.PRIVATE_WINDOWS_GATEWAY:
        raise RuntimeError(
            "private_windows_gateway is disabled until TLS, firewall, certificate, "
            "client-policy, and two-machine qualification pass"
        )
    return profile


def virtual_model_catalog() -> dict[str, dict[str, Any]]:
    """Return the content-free virtual-model discovery contract."""

    return {model.id: asdict(model) for model in _effective_virtual_models()}


def apply_virtual_model(payload: dict[str, Any]) -> VirtualModelPolicy:
    """Apply one server-owned virtual model to a validated request payload."""

    requested = str(payload.get("virtual_model") or "").strip().lower()
    requested_mode = str(payload.get("mode") or "").strip().lower()
    # Simulation is a separate product path (bounded multi-agent). Never admit
    # it through the chat gateway virtual-model contract.
    if requested_mode == "simulation" or requested in {
        "simulation",
        "dle-simulation",
        "dle-simulation.v1",
        "sim",
    }:
        raise ValueError("Unsupported governed virtual model")
    if not requested:
        requested = {
            "enhanced": "dle-enhanced",
            "local_review": "dle-local-review",
        }.get(requested_mode, "dle-standard")
    catalog = {model.id: model for model in _effective_virtual_models()}
    policy = catalog.get(requested)
    if policy is None:
        raise ValueError("Unsupported governed virtual model")
    if requested_mode and requested_mode != policy.mode:
        raise ValueError("virtual_model conflicts with requested execution mode")

    payload["virtual_model"] = policy.id
    payload["mode"] = policy.mode
    constraints = payload.get("constraints")
    if not isinstance(constraints, dict):
        constraints = {}
    requested_calls = constraints.get("max_provider_calls", policy.max_provider_calls)
    try:
        bounded_calls = int(requested_calls)
    except (TypeError, ValueError):
        bounded_calls = policy.max_provider_calls
    constraints["max_provider_calls"] = max(
        0,
        min(policy.max_provider_calls, bounded_calls),
    )
    payload["constraints"] = constraints
    metadata = payload.get("meta")
    if not isinstance(metadata, dict):
        metadata = {}
    metadata["gateway_contract_version"] = GATEWAY_CONTRACT_VERSION
    metadata["virtual_model_manifest_version"] = VIRTUAL_MODEL_MANIFEST_VERSION
    metadata["virtual_model"] = policy.id
    payload["meta"] = metadata
    return policy


def _scope_values(raw: Any) -> Iterable[str]:
    if isinstance(raw, str):
        return (raw,)
    if isinstance(raw, (list, tuple, set, frozenset)):
        return (str(value) for value in raw)
    return ()


def normalize_client_scopes(permissions: Mapping[str, Any] | None) -> frozenset[str]:
    """Normalize explicit scopes and safely map retained legacy key metadata."""

    values = permissions if isinstance(permissions, Mapping) else {}
    explicit = {
        str(scope).strip().lower()
        for scope in _scope_values(values.get("scopes"))
        if str(scope).strip().lower() in CLIENT_SCOPES
    }
    if explicit:
        return frozenset(explicit)

    # Migration compatibility only. Read never grants model execution.
    migrated: set[str] = set()
    if values.get("read"):
        migrated.update({
            "run:read",
            "trace:read",
            "evidence:read",
            "models:read",
            "ka:read",
        })
    if values.get("write") or values.get("chat"):
        migrated.update({"chat", "run:create"})
    if values.get("write"):
        migrated.update({
            "routing:override",
            "ka:plan",
            "ka:execute",
            "ka:cancel",
        })
    if values.get("stream"):
        migrated.add("stream")
    if values.get("run_cancel"):
        migrated.add("run:cancel")
    return frozenset(migrated)


def validate_client_scopes(raw_scopes: Any) -> tuple[str, ...]:
    """Validate scopes accepted when an owner creates or rotates a client key."""

    normalized = tuple(dict.fromkeys(
        str(scope).strip().lower() for scope in _scope_values(raw_scopes)
        if str(scope).strip()
    ))
    unknown = sorted(set(normalized) - CLIENT_SCOPES)
    if unknown:
        raise ValueError(f"Unsupported client scopes: {', '.join(unknown)}")
    if set(normalized) & ADMINISTRATIVE_SCOPES:
        raise ValueError("Administrative scopes cannot be granted to a client key")
    return normalized


def scope_allows(scopes: Iterable[str], required_scope: str) -> bool:
    return str(required_scope).strip().lower() in {
        str(scope).strip().lower() for scope in scopes
    }
