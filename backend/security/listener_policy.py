"""Fail-closed listener policy for Phase 8 gateway profiles."""

from __future__ import annotations

import ipaddress

from backend.llm_gateway.external_contract import resolve_gateway_profile


LOOPBACK_LISTENER_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def resolve_loopback_listener_host(raw_host: str | None, *, default: str = "127.0.0.1") -> str:
    """Return a qualified profile's host; all current profiles stay loopback."""

    # This validates desktop_loopback/same_host_gateway and rejects private mode
    # until its TLS/firewall/two-machine qualification has actually passed.
    resolve_gateway_profile()

    host = (raw_host or default).strip().lower()
    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1]

    if host == "localhost":
        return host

    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise RuntimeError(
            "DataLogicEngine listener host must be localhost or a loopback IP"
        ) from exc

    if not address.is_loopback:
        raise RuntimeError(
            "DataLogicEngine private/public listener exposure is disabled until "
            "the Phase 8 private-listener qualification passes"
        )
    return host
