from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import httpx
import time

from .auth import Auth
from .exceptions import UKGHTTPError, UKGConfigError
from .models import UKGEnvelope


@dataclass
class UKGClientConfig:
    base_url: str
    timeout_s: float = 60.0
    verify_tls: bool = True
    default_headers: Optional[Dict[str, str]] = None

    # Resilience defaults (override per org/policy)
    max_retries: int = 2
    retry_backoff_s: float = 0.5
    retry_max_backoff_s: float = 8.0
    retry_on_status: Tuple[int, ...] = (429, 500, 502, 503, 504)
class UKGClient:
    """HTTP client for the UKG OpenAPI surface."""

    def __init__(self, config: UKGClientConfig, auth: Optional[Auth] = None):
        if not config.base_url:
            raise UKGConfigError("base_url is required")
        self.config = config
        self.auth = auth or Auth()
        self._client = httpx.Client(
            base_url=config.base_url.rstrip("/"),
            timeout=config.timeout_s,
            verify=config.verify_tls,
            headers=config.default_headers or {},
        )

    def close(self) -> None:
        self._client.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Any = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> UKGEnvelope:
        h: Dict[str, str] = {}
        h.update(self.auth.headers())
        if headers:
            h.update(headers)

        # Basic retry loop for transient failures (network/timeouts, 429/5xx).
        attempt = 0
        while True:
            try:
                resp = self._client.request(method, path, params=params, json=json_body, headers=h)
                if resp.status_code in self.config.retry_on_status and attempt < self.config.max_retries:
                    retry_after = resp.headers.get('retry-after')
                    if retry_after:
                        try:
                            sleep_s = max(0.0, float(retry_after))
                        except ValueError:
                            sleep_s = self.config.retry_backoff_s
                    else:
                        sleep_s = min(self.config.retry_max_backoff_s, self.config.retry_backoff_s * (2 ** attempt))
                        sleep_s *= (0.75 + (0.5 * __import__('random').random()))
                    time.sleep(sleep_s)
                    attempt += 1
                    continue
                break
            except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError):
                if attempt >= self.config.max_retries:
                    raise
                sleep_s = min(self.config.retry_max_backoff_s, self.config.retry_backoff_s * (2 ** attempt))
                sleep_s *= (0.75 + (0.5 * __import__('random').random()))
                time.sleep(sleep_s)
                attempt += 1
        content_type = resp.headers.get("content-type", "")
        if resp.status_code >= 400:
            detail = None
            if "application/json" in content_type:
                try:
                    detail = resp.json()
                except Exception:
                    detail = resp.text
            else:
                detail = resp.text
            raise UKGHTTPError(resp.status_code, resp.reason_phrase, detail=detail)

        if "application/json" in content_type:
            data = resp.json()
        else:
            data = resp.text

        return UKGEnvelope(
            data=data,
            trace_id=resp.headers.get("x-trace-id") or resp.headers.get("trace-id"),
            request_id=resp.headers.get("x-request-id") or resp.headers.get("request-id"),
            warnings=[],
        )