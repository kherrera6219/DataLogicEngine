"""
Server-Side Request Forgery (SSRF) outbound URL safeguards.
"""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from typing import Iterable, Optional, Set
from urllib.parse import urlparse


class SSRFProtectionError(ValueError):
    """Raised when an outbound URL violates SSRF policy."""


@dataclass(frozen=True)
class OutboundURLValidationResult:
    url: str
    hostname: str
    resolved_ips: tuple[str, ...]


def normalize_host_tokens(values: Optional[Iterable[str] | str]) -> set[str]:
    if values is None:
        return set()
    if isinstance(values, str):
        candidates = [token.strip() for token in values.split(",")]
    else:
        candidates = [str(token).strip() for token in values]
    return {token.lower().rstrip(".") for token in candidates if token}


def _host_allowed(hostname: str, allowed_hosts: set[str]) -> bool:
    if not allowed_hosts:
        return True
    if hostname in allowed_hosts:
        return True
    for token in allowed_hosts:
        if token.startswith("*.") and hostname.endswith(token[1:]):
            return True
    return False


def _is_disallowed_ip(
    ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address,
    allow_private_hosts: bool,
) -> bool:
    if ip_obj.is_multicast or ip_obj.is_reserved or ip_obj.is_unspecified:
        return True
    if not allow_private_hosts and (ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local):
        return True
    if allow_private_hosts and ip_obj.is_link_local:
        return True
    return False


def validate_outbound_url(
    url: str,
    *,
    allowed_hosts: Optional[Iterable[str] | str] = None,
    allow_private_hosts: bool = False,
) -> OutboundURLValidationResult:
    """
    Validate an outbound URL against SSRF controls.

    Controls:
    - Scheme must be HTTP/HTTPS.
    - Credentials in URL are forbidden.
    - Host must be allowlisted when allowlist is provided.
    - Resolved IPs must not target blocked ranges.
    """
    parsed = urlparse(url or "")
    if parsed.scheme.lower() not in {"http", "https"}:
        raise SSRFProtectionError("Only http/https outbound URLs are allowed.")
    if parsed.username or parsed.password:
        raise SSRFProtectionError("Credentials in outbound URL are not allowed.")

    hostname = (parsed.hostname or "").strip().lower().rstrip(".")
    if not hostname:
        raise SSRFProtectionError("Outbound URL must include a hostname.")

    allowlist = normalize_host_tokens(allowed_hosts)
    if not _host_allowed(hostname, allowlist):
        raise SSRFProtectionError(f"Outbound hostname '{hostname}' is not in the allowlist.")

    resolved_ips: Set[str] = set()
    try:
        addr_info = socket.getaddrinfo(hostname, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise SSRFProtectionError(f"Unable to resolve outbound hostname '{hostname}'.") from exc

    for record in addr_info:
        ip_str = record[4][0]
        ip_obj = ipaddress.ip_address(ip_str)
        if _is_disallowed_ip(ip_obj, allow_private_hosts=allow_private_hosts):
            raise SSRFProtectionError(f"Outbound hostname '{hostname}' resolved to disallowed address '{ip_str}'.")
        resolved_ips.add(ip_str)

    if not resolved_ips:
        raise SSRFProtectionError(f"Outbound hostname '{hostname}' did not resolve to usable addresses.")

    return OutboundURLValidationResult(
        url=url,
        hostname=hostname,
        resolved_ips=tuple(sorted(resolved_ips)),
    )


def assert_safe_outbound_url(
    url: str,
    *,
    allowed_hosts: Optional[Iterable[str] | str] = None,
    allow_private_hosts: bool = False,
) -> None:
    """Raise SSRFProtectionError if URL fails validation."""
    validate_outbound_url(url, allowed_hosts=allowed_hosts, allow_private_hosts=allow_private_hosts)
