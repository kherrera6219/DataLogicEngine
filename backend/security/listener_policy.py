"""Fail-closed listener policy for the pre-Phase-8 desktop runtime."""

from __future__ import annotations

import ipaddress


LOOPBACK_LISTENER_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def resolve_loopback_listener_host(raw_host: str | None, *, default: str = "127.0.0.1") -> str:
    """Return an approved loopback bind host or reject private/public exposure.

    Private-network listener qualification is deliberately deferred to Phase 8.
    Until then, every supported entry point must bind to loopback only.
    """

    host = (raw_host or default).strip().lower()
    if host.startswith("[") and host.endswith("]"):
        host = host[1:-1]

    if host == "localhost":
        return host

    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise RuntimeError(
            "DataLogicEngine listener host must be localhost or a loopback IP before Phase 8"
        ) from exc

    if not address.is_loopback:
        raise RuntimeError(
            "DataLogicEngine private/public listener exposure is disabled until Phase 8 qualification"
        )
    return host
