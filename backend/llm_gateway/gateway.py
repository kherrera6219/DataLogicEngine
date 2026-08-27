# ruff: noqa: E402
"""Provider boundary and compatibility adapter for governed execution.

The backend-owned :class:`GovernedExecutionOrchestrator` is the only product
request pipeline. This module owns provider selection, bounded calls, usage, and
the legacy ``GatewayRequest``/``GatewayResponse`` transport adapter.
"""

import asyncio
import logging
import os
import uuid
from datetime import datetime, UTC, timedelta
from pathlib import Path
from typing import Any, AsyncIterator, Optional
from dataclasses import dataclass, field
from sqlalchemy.exc import SQLAlchemyError

from models import LLMProvider, LLMProviderUsage, ChatSession, ChatMessage
from backend.llm_gateway.completion import (
    CompletionDisposition,
    ProviderCompletion,
)
from backend.utils.error_normalization import normalize_public_error_message
from backend.llm_gateway.governance import AIGovernanceEngine
from backend.llm_gateway.model_defaults import (
    default_model_for_provider,
)
from backend.llm_gateway.provider_manifest import (
    PROVIDERS,
    normalize_provider_type,
    provider_definition,
    validate_provider_model,
)
from backend.llm_gateway.providers import GoogleProvider, OpenAIProvider

logger = logging.getLogger(__name__)


@dataclass
class GatewayRequest:
    """Incoming gateway request."""
    messages: list[dict[str, Any]]
    provider: Optional[str] = None
    model: Optional[str] = None
    mode: str = "chat"  # chat, explain, trace
    constraints: dict[str, Any] = field(default_factory=dict)
    run_ukg_pipeline: bool = True
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    api_key_id: Optional[str] = None
    meta: dict[str, Any] = field(default_factory=dict)  # For 17-axis coordinate hints


@dataclass
class GatewayResponse:
    """Gateway response with UKG enhancements."""
    content: str
    run_id: str
    provider_used: str
    model_used: str
    usage: dict[str, Any]
    completion: Optional[dict[str, Any]] = None
    ok: bool = True
    # UKG enhancements
    coordinate: Any = None
    tier: Optional[str] = None
    layers: Optional[list[str]] = None
    trace: Optional[list[dict]] = None
    explainability: Optional[dict] = None
    confidence: Optional[float] = None
    confidence_measurement: Optional[dict[str, Any]] = None
    convergence: Optional[dict[str, Any]] = None
    claims: list[dict[str, Any]] = field(default_factory=list)
    citations: list[dict[str, Any]] = field(default_factory=list)
    validators: list[dict[str, Any]] = field(default_factory=list)
    evidence_count: int = 0
    warnings: list[str] = field(default_factory=list)
    error: Optional[str] = None
    meta: dict[str, Any] = field(default_factory=dict)
    contract_version: str = "governed.v1"
    status: str = "completed"
    failure: Optional[dict[str, Any]] = None


@dataclass(frozen=True)
class ChatMessagePersistenceResult:
    """Typed result that distinguishes transcript failure from success."""

    ok: bool
    code: str
    session_id: Optional[str] = None
    message_id: Optional[str] = None
    run_id: Optional[str] = None
    rag_status: str = "not_attempted"


class CircuitBreaker:
    """Simple Circuit Breaker for LLM Providers."""
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.last_failure_time: Optional[datetime] = None

    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if self.last_failure_time and (datetime.now(UTC) - self.last_failure_time).total_seconds() > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        return True  # HALF_OPEN

    def record_success(self):
        self.failures = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = datetime.now(UTC)
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(f"Circuit Breaker for {self.name} is now OPEN")


class NetworkState:
    """Cached local-first provider reachability state for desktop/VM status."""

    _last_checked: Optional[datetime] = None
    _last_result: dict[str, Any] = {}
    _ttl_seconds = 30

    @classmethod
    def check(cls, *, force: bool = False) -> dict[str, Any]:
        now = datetime.now(UTC)
        if (
            not force
            and cls._last_checked is not None
            and now - cls._last_checked < timedelta(seconds=cls._ttl_seconds)
            and cls._last_result
        ):
            return dict(cls._last_result)

        providers = cls._configured_providers()
        # A stored key proves configuration, not reachability or entitlement.
        # Only the explicit provider-test path may promote this to available.
        state = "CONFIGURED" if providers else "OFFLINE"
        active_provider = providers[0] if providers else None
        cls._last_checked = now
        cls._last_result = {
            "state": state,
            "last_checked": now.isoformat(),
            "active_provider": active_provider,
            "provider_status": "stored" if providers else "not_configured",
            "details": {
                "configured_providers": providers,
                "ttl_seconds": cls._ttl_seconds,
            },
        }
        return dict(cls._last_result)

    @staticmethod
    def _configured_providers() -> list[str]:
        providers: list[str] = []
        for provider in PROVIDERS:
            if any(os.environ.get(env_name) for env_name in provider.api_key_environment):
                providers.append(provider.id)

        # Also count providers configured in the database (keys saved through the
        # Settings UI). Without this the desktop app reports OFFLINE even after a
        # user saves an API key, because no matching *_API_KEY env var is present.
        for provider_type in NetworkState._db_configured_provider_types():
            if provider_type not in providers:
                providers.append(provider_type)
        return providers

    @staticmethod
    def _db_configured_provider_types() -> list[str]:
        """Active LLM provider types that have a stored API key, from the DB.

        Best-effort and context-safe: may be called outside a Flask request, so it
        pushes an app context when one is available and never raises.
        """
        def _query() -> list[str]:
            rows = LLMProvider.query.filter_by(is_active=True).all()
            types: list[str] = []
            for row in rows:
                if getattr(row, "api_key_encrypted", None):
                    provider_type = str(getattr(row, "provider_type", "") or "").strip().lower()
                    try:
                        provider_type = normalize_provider_type(provider_type)
                    except ValueError:
                        continue
                    if provider_type not in types:
                        types.append(provider_type)
            return types

        try:
            from flask import current_app as _cur_app
            try:
                app = _cur_app._get_current_object()
            except RuntimeError:
                app = None
            if app is not None:
                with app.app_context():
                    return _query()
            return _query()
        except Exception as exc:  # pragma: no cover - defensive, status path only
            logger.debug("DB provider status lookup failed: %s", exc)
            return []

class LLMGateway:
    """
    Main gateway class that routes requests through UKG SDK.
    """
    
    # Class-level circuit breaker state
    _circuit_breakers: dict[str, CircuitBreaker] = {}
    _last_quad_analysis_status: dict[str, Any] = {
        "pod_count": 0,
        "collective_confidence": 0.0,
        "mode": "idle",
        "status": "idle",
    }
    
    def __init__(self, db_session=None):
        self.db = db_session
        self._overlays: dict[str, Any] = {}
        self._governance = AIGovernanceEngine(db_session)
    
    def _get_circuit_breaker(self, provider_id: str) -> CircuitBreaker:
        if provider_id not in self._circuit_breakers:
            self._circuit_breakers[provider_id] = CircuitBreaker(provider_id)
        return self._circuit_breakers[provider_id]

    @classmethod
    def get_quad_analysis_status(cls) -> dict[str, Any]:
        """Return the latest compact quad-analysis status for desktop IPC."""
        return dict(cls._last_quad_analysis_status)

    @staticmethod
    def _normalize_allowlist(values: Any) -> set[str]:
        """Normalize policy allowlists to lower-case sets."""
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, (list, tuple, set)):
            return set()

        normalized: set[str] = set()
        for value in values:
            if value is None:
                continue
            text = str(value).strip().lower()
            if text:
                normalized.add(text)
        return normalized

    def _provider_matches_policy(self, provider: Any, allowed_provider_types: set[str]) -> bool:
        """Return True when provider matches the allowed provider policy."""
        provider_type = str(getattr(provider, "provider_type", "") or "").strip().lower()
        provider_name = str(getattr(provider, "name", "") or "").strip().lower()
        provider_family = provider_name.split("-", 1)[0] if provider_name else ""

        return (
            provider_type in allowed_provider_types
            or provider_name in allowed_provider_types
            or provider_family in allowed_provider_types
        )

    @staticmethod
    def _desktop_local_first_enabled() -> bool:
        """Return True when the gateway should prefer local desktop fallback behavior."""
        return os.environ.get("IS_DESKTOP_APP", "false").lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _has_active_cloud_providers() -> bool:
        """Return True when at least one T4/T5 cloud provider is active in the DB.

        The user's explicit act of saving a Google or OpenAI API key via Settings
        is the gate for cloud escalation — no separate feature-flag is needed.
        Both ``is_active=True`` AND a stored ``api_key_encrypted`` are required so
        that empty stub provider records never accidentally unlock cloud routing.
        """
        _CLOUD_TYPES: frozenset[str] = frozenset({"google", "gemini", "openai"})

        def _query() -> bool:
            rows = LLMProvider.query.filter_by(is_active=True).all()
            for row in rows:
                pt = str(getattr(row, "provider_type", "") or "").strip().lower()
                if pt in _CLOUD_TYPES and getattr(row, "api_key_encrypted", None):
                    return True
            return False

        try:
            from flask import current_app as _cur_app
            try:
                app = _cur_app._get_current_object()
            except RuntimeError:
                app = None
            if app is not None:
                with app.app_context():
                    return _query()
            return _query()
        except Exception as exc:
            logger.debug("Cloud provider check failed (non-fatal): %s", exc)
            return False

    @staticmethod
    def _resolve_model(request: GatewayRequest, provider_record: Optional[LLMProvider]) -> str:
        provider_type = normalize_provider_type(
            str(getattr(provider_record, "provider_type", "") or request.provider or "")
        )
        selected_model = request.model
        if not selected_model and provider_record and getattr(provider_record, "model_id", None):
            selected_model = str(provider_record.model_id)
        return validate_provider_model(provider_type, selected_model)

    @staticmethod
    def _positive_int(value: Any, default: int, minimum: int = 1, maximum: int = 60) -> int:
        """Parse bounded positive integer with sane defaults."""
        if isinstance(value, bool):
            return default
        if not isinstance(value, (int, str)):
            return default
        try:
            parsed = int(str(value).strip())
        except (TypeError, ValueError):
            return default
        if parsed < minimum:
            return default
        return min(parsed, maximum)

    @staticmethod
    def _preferred_env_provider() -> str | None:
        """Return a supported provider preference for env-only fallback routing."""
        preferred = (
            os.environ.get("LLM_DEFAULT_PROVIDER")
            or os.environ.get("AI_PROVIDER")
            or ""
        ).strip().lower()
        if preferred == "gemini":
            preferred = "google"
        return preferred if preferred in {"openai", "google"} else None

    @staticmethod
    def _env_provider_sort_key(provider_record: Any) -> tuple[int, int]:
        preferred = LLMGateway._preferred_env_provider()
        provider_type = str(getattr(provider_record, "provider_type", "") or "").strip().lower()
        if provider_type == "gemini":
            provider_type = "google"
        priority = getattr(provider_record, "priority", 10)
        return (0 if preferred and provider_type == preferred else 1, priority)

    @staticmethod
    def _runtime_data_root() -> Path:
        """Return a writable runtime data root for desktop/packaged execution."""
        settings_path = os.environ.get("DATALOGIC_STORAGE_SETTINGS_PATH")
        if settings_path:
            return Path(settings_path).expanduser().resolve().parent
        return Path.cwd()

    def _provider_timeout_seconds(self, provider_record: Any) -> int:
        env_default = self._positive_int(os.environ.get("LLM_PROVIDER_TIMEOUT_SECONDS"), 30, minimum=1, maximum=300)
        return self._positive_int(getattr(provider_record, "timeout_seconds", None), env_default, minimum=1, maximum=300)

    def _provider_max_retries(self, provider_record: Any) -> int:
        env_default = self._positive_int(os.environ.get("LLM_PROVIDER_MAX_RETRIES"), 3, minimum=1, maximum=10)
        return self._positive_int(getattr(provider_record, "max_retries", None), env_default, minimum=1, maximum=10)

    @staticmethod
    def _is_rate_limit_error(error: Optional[str]) -> bool:
        """Return True when the provider error is a rate-limit / quota signal (HTTP 429).

        Rate limiting is NOT a provider failure — the provider is healthy, just
        throttling.  Callers use this to skip circuit-breaker accounting and to
        surface the error directly to the client instead of queuing offline.
        """
        if not error:
            return False
        lowered = str(error).lower()
        return any(
            m in lowered
            for m in ("429", "rate limit", "rate_limit", "quota exceeded", "insufficient_quota", "billing")
        )

    @staticmethod
    def _is_retryable_error(error: Optional[str]) -> bool:
        """Classify retryable failures for provider failover attempts.

        Rate-limit errors (429) are intentionally excluded: they are handled
        separately by _is_rate_limit_error and should never be retried with a
        short backoff (the rate-limit window resets on the provider's side, not
        after a few milliseconds of sleep).
        """
        if not error:
            return False

        lowered = str(error).lower()
        non_retryable_markers = (
            "401",
            "403",
            "invalid api key",
            "authentication",
            "unauthorized",
            "forbidden",
            "not allowed",
            "unsupported model",
            "invalid request",
            # Rate limiting is handled separately — not retried, not a circuit failure.
            "429",
            "rate limit",
            "rate_limit",
            "quota exceeded",
            "insufficient_quota",
            "billing",
        )
        if any(marker in lowered for marker in non_retryable_markers):
            return False

        retryable_markers = (
            "timeout",
            "timed out",
            "500",
            "502",
            "503",
            "504",
            "temporar",
            "connection reset",
            "connection aborted",
            "network",
            "service unavailable",
        )
        if any(marker in lowered for marker in retryable_markers):
            return True

        # Unknown errors fail closed. Retrying them can duplicate non-idempotent
        # work and masks contract/provider bugs as transient network incidents.
        return False

    @staticmethod
    async def _retry_backoff_sleep(attempt: int) -> None:
        import random

        sleep_time = (2 ** attempt) + random.uniform(0, 1)
        await asyncio.sleep(sleep_time)

    @staticmethod
    def _public_error_message(error: Optional[str]) -> str:
        """Return a safe, normalized API error message."""
        return normalize_public_error_message(
            raw_error=error,
            fallback="LLM provider request failed",
            safe_fragments=(
                "requested model",
                "not allowed",
                "no active providers found",
                "no provider configured",
                # Rate-limit messages are safe to surface — they help the user
                # understand why the request was not processed.
                "rate limit",
                "rate limited",
                "rate_limit",
                "quota exceeded",
                "insufficient_quota",
                # Intentional policy blocks from the governed security path — the user
                # should see a policy message, not a fake provider failure.
                "blocked by security policy",
            ),
        )
    
    async def execute(self, request):
        """Execute the canonical versioned governed contract."""

        from backend.governed_execution.contracts import GovernedRequest
        from backend.governed_execution.orchestrator import GovernedExecutionOrchestrator

        governed_request = request if isinstance(request, GovernedRequest) else GovernedRequest.from_gateway(request)
        return await GovernedExecutionOrchestrator(self).execute(governed_request)

    async def process(self, request: GatewayRequest) -> GatewayResponse:
        """Compatibility adapter into the canonical governed contract."""

        governed = await self.execute(request)
        return self._gateway_response_from_governed(governed, request)

    @staticmethod
    def _gateway_response_from_governed(governed, request: GatewayRequest) -> GatewayResponse:
        usage = dict(governed.usage or {})
        usage.setdefault("tokens_in", usage.get("prompt_tokens", 0))
        usage.setdefault("tokens_out", usage.get("completion_tokens", 0))
        return GatewayResponse(
            content=governed.answer,
            run_id=governed.trace_id,
            provider_used=governed.provider_used or "none",
            model_used=governed.model_used or request.model or "unknown",
            usage=usage,
            completion=governed.completion.to_dict()
            if governed.completion
            else None,
            ok=governed.ok,
            coordinate=governed.coordinate,
            tier=governed.tier,
            layers=[stage.name for stage in governed.stages],
            trace=[stage.to_dict() for stage in governed.stages],
            explainability={
                "output_classification": (governed.metadata.get("validation") or {}).get("classification")
            }
            if isinstance(governed.metadata, dict) and governed.metadata.get("validation")
            else None,
            confidence=governed.confidence,
            confidence_measurement=governed.confidence_measurement.to_dict()
            if governed.confidence_measurement
            else None,
            convergence=governed.convergence.to_dict() if governed.convergence else None,
            claims=[claim.to_dict() for claim in governed.claims],
            citations=[citation.to_dict() for citation in governed.citations],
            validators=[validator.to_dict() for validator in governed.validators],
            evidence_count=len(governed.evidence),
            warnings=list(governed.warnings),
            error=governed.failure.message if governed.failure else None,
            meta=dict(governed.metadata),
            contract_version=governed.contract_version,
            status=governed.status,
            failure=governed.failure.to_dict() if governed.failure else None,
        )

    async def process_stream(self, request: GatewayRequest) -> AsyncIterator[dict[str, Any]]:
        """Emit live governed stage events and validated answer deltas."""
        from backend.governed_execution.contracts import GovernedRequest
        from backend.governed_execution.orchestrator import GovernedExecutionOrchestrator

        governed_request = (
            request
            if isinstance(request, GovernedRequest)
            else GovernedRequest.from_gateway(request)
        )
        events: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=256)
        sequence = 0

        def event_sink(trace_id: str, stage: dict[str, Any]) -> None:
            nonlocal sequence
            sequence += 1
            payload = {
                "type": "stage",
                "event": "stage.progress",
                "event_id": sequence,
                "delivery_mode": "live_governed_stage",
                "run_id": trace_id,
                "stage": stage,
            }
            try:
                events.put_nowait(payload)
            except asyncio.QueueFull:
                # Never block governed execution on a slow client. The final
                # trace remains authoritative and the stream reports the gap.
                try:
                    events.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                events.put_nowait({
                    "type": "warning",
                    "event": "stream.backpressure",
                    "event_id": sequence,
                    "delivery_mode": "live_governed_stage",
                    "run_id": trace_id,
                    "code": "STREAM_EVENT_DROPPED",
                })

        execution = asyncio.create_task(
            GovernedExecutionOrchestrator(self, event_sink=event_sink).execute(governed_request)
        )
        try:
            while not execution.done() or not events.empty():
                try:
                    event = events.get_nowait()
                except asyncio.QueueEmpty:
                    event_wait = asyncio.create_task(events.get())
                    done, _ = await asyncio.wait(
                        {execution, event_wait},
                        timeout=15.0,
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    if event_wait in done:
                        event = event_wait.result()
                    else:
                        event_wait.cancel()
                        if execution in done:
                            continue
                        sequence += 1
                        yield {
                            "type": "heartbeat",
                            "event": "stream.heartbeat",
                            "event_id": sequence,
                            "delivery_mode": "live_governed_stage",
                            "request_id": governed_request.request_id,
                        }
                        continue
                yield event
            governed = await execution
        finally:
            if not execution.done():
                execution.cancel()
                try:
                    await execution
                except asyncio.CancelledError:
                    pass

        response = self._gateway_response_from_governed(governed, governed_request)
        if not response.ok:
            yield {
                "type": "error",
                "event": "stream.error",
                "delivery_mode": "live_governed_stage",
                "error": response.error or "Gateway failed",
                "run_id": response.run_id,
                "provider_used": response.provider_used,
                "model_used": response.model_used,
            }
            return

        if response.evidence_count:
            sequence += 1
            yield {
                "type": "evidence",
                "event": "evidence.ready",
                "event_id": sequence,
                "delivery_mode": "validated_output",
                "run_id": response.run_id,
                "evidence_count": response.evidence_count,
                "citations": response.citations or [],
            }

        sequence += 1
        yield {
            "type": "validation",
            "event": "validation.completed",
            "event_id": sequence,
            "delivery_mode": "validated_output",
            "run_id": response.run_id,
            "confidence_measurement": response.confidence_measurement,
            "convergence": response.convergence,
        }

        content = response.content or ""
        chunk_size = 256
        for index in range(0, len(content), chunk_size):
            await asyncio.sleep(0)
            sequence += 1
            yield {
                "type": "chunk",
                "event": "content.delta",
                "event_id": sequence,
                "delivery_mode": "validated_output",
                "index": index // chunk_size,
                "content": content[index:index + chunk_size],
                "run_id": response.run_id,
                "provider_used": response.provider_used,
                "model_used": response.model_used,
            }

        sequence += 1
        yield {
            "type": "done",
            "event": "stream.completed",
            "event_id": sequence,
            "delivery_mode": "validated_output",
            "run_id": response.run_id,
            "provider_used": response.provider_used,
            "model_used": response.model_used,
            "usage": response.usage,
            "completion": response.completion,
        }

    def _create_sdk_provider(self, provider_record: Optional[LLMProvider]) -> Any:
        """Create a backend-owned async adapter for a supported provider."""
        if not provider_record:
            raise ValueError("No provider configured")

        provider_type = normalize_provider_type(
            str(getattr(provider_record, "provider_type", "") or "")
        )
        definition = provider_definition(provider_type)
        api_key = None
        try:
            api_key = provider_record.get_api_key()
        except Exception as exc:
            logger.warning("Failed to decrypt API key for %s: %s", provider_record.name, exc)

        if not api_key:
            api_key = next(
                (os.environ.get(name) for name in definition.api_key_environment if os.environ.get(name)),
                None,
            )
        if not api_key:
            raise ValueError(f"No API key available for {provider_type}")

        timeout_seconds = self._provider_timeout_seconds(provider_record)
        if provider_type == "openai":
            return OpenAIProvider(
                api_key=api_key,
                base_url=getattr(provider_record, "endpoint", None),
                timeout_seconds=timeout_seconds,
            )
        if provider_type == "google":
            return GoogleProvider(api_key=api_key, timeout_seconds=timeout_seconds)
        raise ValueError(f"Unsupported provider: {provider_type}")

    async def _get_eligible_providers(
        self,
        preferred_name: Optional[str] = None,
        meta: dict = None,
        allowed_provider_types: Optional[set[str]] = None,
        allowed_models: Optional[set[str]] = None,
    ) -> list[LLMProvider]:
        """Return exactly one explicitly selected supported provider.

        The provider manifest is authoritative. This method never synthesizes a
        cross-provider fallback chain and never maps an unknown value to OpenAI.
        """
        class EnvProvider:
            def __init__(self, provider_type: str, priority: int) -> None:
                definition = provider_definition(provider_type)
                self.id = f"env:{provider_type}"
                self.name = provider_type
                self.provider_type = provider_type
                self.endpoint = None
                self.deployment_name = None
                self.api_version = None
                self.model_id = definition.default_model
                self.priority = priority
                self.is_default = False
                self.timeout_seconds = LLMGateway._positive_int(
                    os.environ.get("LLM_PROVIDER_TIMEOUT_SECONDS"),
                    30,
                    minimum=1,
                    maximum=300,
                )
                self.max_retries = LLMGateway._positive_int(
                    os.environ.get("LLM_PROVIDER_MAX_RETRIES"),
                    2,
                    minimum=1,
                    maximum=2,
                )

            @staticmethod
            def get_api_key() -> None:
                return None

        try:
            from flask import current_app as _current_app

            try:
                app = _current_app._get_current_object()
            except RuntimeError:
                app = None

            def _query_db() -> list[Any]:
                return LLMProvider.query.filter_by(is_active=True).order_by(LLMProvider.priority).all()

            if app is not None:
                with app.app_context():
                    providers: list[Any] = _query_db()
            else:
                providers = _query_db()
        except Exception as exc:
            logger.warning("Failed to query providers from DB: %s", exc)
            providers = []

        supported_rows: list[Any] = []
        for provider in providers:
            try:
                provider.provider_type = normalize_provider_type(provider.provider_type)
            except (AttributeError, ValueError):
                continue
            supported_rows.append(provider)

        present_types = {provider.provider_type for provider in supported_rows}
        candidates = list(supported_rows)
        for priority, definition in enumerate(PROVIDERS, start=1000):
            if definition.id in present_types:
                continue
            if any(os.environ.get(name) for name in definition.api_key_environment):
                candidates.append(EnvProvider(definition.id, priority))

        normalized_allowed_types: set[str] = set()
        for value in allowed_provider_types or set():
            try:
                normalized_allowed_types.add(normalize_provider_type(value))
            except ValueError:
                continue
        if normalized_allowed_types:
            candidates = [
                provider for provider in candidates if provider.provider_type in normalized_allowed_types
            ]

        requested_type: str | None = None
        if preferred_name:
            try:
                requested_type = normalize_provider_type(preferred_name)
            except ValueError:
                named = next(
                    (
                        provider
                        for provider in candidates
                        if str(getattr(provider, "name", "")).strip().lower()
                        == str(preferred_name).strip().lower()
                    ),
                    None,
                )
                if named is None:
                    return []
                requested_type = named.provider_type
        if requested_type:
            candidates = [
                provider for provider in candidates if provider.provider_type == requested_type
            ]

        if allowed_models:
            normalized_models = {str(model).strip().lower() for model in allowed_models}
            candidates = [
                provider
                for provider in candidates
                if str(getattr(provider, "model_id", "") or default_model_for_provider(provider.provider_type)).strip().lower()
                in normalized_models
            ]

        if not candidates:
            return []

        if requested_type:
            selected = candidates[0]
        else:
            operator_default = self._preferred_env_provider()
            selected = next(
                (
                    provider
                    for provider in candidates
                    if operator_default and provider.provider_type == operator_default
                ),
                None,
            )
            selected = selected or next(
                (provider for provider in candidates if bool(getattr(provider, "is_default", False))),
                None,
            )
            selected = selected or sorted(candidates, key=self._env_provider_sort_key)[0]
        return [selected]

    @staticmethod
    def _parse_uuid_or_none(value: Any) -> Optional[uuid.UUID]:
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        text = str(value).strip()
        if not text or text.lower() in {"anonymous", "none", "null"}:
            return None
        try:
            return uuid.UUID(text)
        except (TypeError, ValueError, AttributeError):
            return None

    @staticmethod
    def _parse_int_or_none(value: Any) -> Optional[int]:
        if value is None:
            return None
        text = str(value).strip()
        if not text or text.lower() in {"anonymous", "none", "null"}:
            return None
        try:
            return int(text)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _normalize_trace_status(value: Any) -> str:
        status = str(value or "completed").strip().lower()
        return {
            "ok": "completed",
            "pass": "completed",
            "success": "completed",
            "fail": "failed",
            "error": "failed",
        }.get(status, status)

    @staticmethod
    def _parse_trace_datetime(value: Any) -> Optional[datetime]:
        if isinstance(value, datetime):
            return value
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _dsqp_profiles_from_output(output: Any) -> Optional[dict[str, Any]]:
        if not isinstance(output, dict):
            return None
        profiles = output.get("profiles")
        if isinstance(profiles, dict):
            return profiles
        profiles = output.get("constructed_persona_profiles")
        if isinstance(profiles, dict):
            return profiles
        chain = output.get("dsqp_chain")
        if isinstance(chain, dict) and isinstance(chain.get("profiles"), dict):
            return chain["profiles"]
        return None

    async def _create_trace_run(
        self,
        sdk_result: dict[str, Any],
        query: str,
        run_id: str,
        user_id: str,
        session_id: Optional[str],
        model: str,
    ) -> bool:
        """Persist the canonical governed trace through one transaction."""

        from backend.governed_execution.trace_persistence import persist_governed_trace

        return persist_governed_trace(
            self,
            sdk_result,
            query=query,
            run_id=run_id,
            user_id=user_id,
            session_id=session_id,
            model=model,
        )

    async def _direct_llm_call(
        self,
        sdk_provider: Any,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Execute one orchestrator-authorized provider call."""
        if sdk_provider is None:
            return {"ok": False, "error": "No provider configured"}
        
        try:
            response = await sdk_provider.complete(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            # Some providers signal errors via response.raw["ok"] == False rather
            # than raising; check the sentinel so those failures propagate correctly.
            raw = response.raw if isinstance(response.raw, dict) else {}
            if raw.get("ok") is False:
                return {
                    "ok": False,
                    "error": raw.get("error", "Local model returned empty response"),
                    "retryable": raw.get("retryable", False),
                    "usage": {},
                }
            completion = (
                response.completion
                if isinstance(response.completion, ProviderCompletion)
                else ProviderCompletion(
                    disposition=CompletionDisposition.PROVIDER_INCOMPLETE,
                    native_reason="metadata_unavailable",
                    response_id=raw.get("response_id"),
                )
            )
            if completion.disposition in {
                CompletionDisposition.SAFETY_BLOCKED,
                CompletionDisposition.FAILED,
            }:
                return {
                    "ok": False,
                    "error": "Provider did not return releasable output",
                    "retryable": False,
                    "usage": response.usage or {},
                    "completion": completion.to_dict(),
                    "failure": {
                        "class": "provider_response",
                        "code": (
                            "PROVIDER_SAFETY_BLOCK"
                            if completion.disposition
                            is CompletionDisposition.SAFETY_BLOCKED
                            else "PROVIDER_COMPLETION_FAILED"
                        ),
                        "replayable": False,
                    },
                }
            return {
                "ok": True,
                "answer": response.text,
                "usage": response.usage or {},
                "completion": completion.to_dict(),
            }
        except Exception as e:
            return {"ok": False, "error": str(e), "exception": e}
    
    async def _record_usage(
        self,
        provider_id: Optional[uuid.UUID],
        provider_type: str,
        user_id: Optional[int],
        api_key_id: Optional[str],
        run_id: str,
        session_id: Optional[str],
        model: Optional[str],
        tokens_in: int,
        tokens_out: int,
        latency_ms: int,
        success: bool,
        estimated_cost_usd: Optional[float] = None,
        purpose: str = "answer",
        request_stage: str = "provider_execution",
        attempt_number: int = 1,
        retry_index: int = 0,
        status: str = "completed",
        error_class: Optional[str] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        disclosed_categories: Optional[list[str]] = None,
        idempotency_key: Optional[str] = None,
        started_at: Optional[datetime] = None,
        ended_at: Optional[datetime] = None,
    ) -> bool:
        """Persist one secret-free provider attempt in the durable ledger."""
        try:
            try:
                from extensions import db
            except ImportError:
                import os
                import sys
                sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                from extensions import db

            def _parse_uuid(value: Any) -> Optional[uuid.UUID]:
                if value is None:
                    return None
                if isinstance(value, uuid.UUID):
                    return value
                try:
                    return uuid.UUID(str(value))
                except (TypeError, ValueError, AttributeError):
                    return None

            provider_uuid = _parse_uuid(provider_id)

            usage_payload = {
                "provider_id": provider_uuid,
                "provider_type": provider_type,
                "user_id": user_id,
                "api_key_id": _parse_uuid(api_key_id),
                "run_id": _parse_uuid(run_id),
                "session_id": str(session_id) if session_id else None,
                "model": model,
                "purpose": purpose,
                "request_stage": request_stage,
                "attempt_number": max(1, int(attempt_number)),
                "retry_index": max(0, int(retry_index)),
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "latency_ms": latency_ms,
                "pricing_status": "available" if estimated_cost_usd is not None else "unknown",
                "status": status,
                "success": success,
                "error_class": error_class,
                "disclosed_categories": sorted(set(disclosed_categories or [])),
                "idempotency_key": idempotency_key,
                "started_at": started_at,
                "ended_at": ended_at,
            }

            if hasattr(LLMProviderUsage, "estimated_cost_usd") and estimated_cost_usd is not None:
                usage_payload["estimated_cost_usd"] = float(estimated_cost_usd)

            if hasattr(LLMProviderUsage, "error_code") and error_code:
                usage_payload["error_code"] = error_code
            if hasattr(LLMProviderUsage, "error_message") and error_message:
                usage_payload["error_message"] = normalize_public_error_message(
                    raw_error=error_message,
                    fallback="Provider request failed",
                )[:500]

            db.session.add(LLMProviderUsage(**usage_payload))
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise

            if provider_uuid:
                provider = LLMProvider.query.get(provider_uuid)
                if provider:
                    provider.last_used_at = datetime.now(UTC)
                    db.session.commit()
            return True
                    
        except Exception as e:
            logger.error("Failed to record provider usage ledger event: %s", e)
            return False
    
    async def close(self) -> None:
        """Clean up."""
        self._overlays.clear()

    async def _save_chat_message(
        self,
        session_id: str,
        user_id: Optional[int],
        role: str,
        content: str,
        run_id: Optional[str] = None,
    ) -> ChatMessagePersistenceResult:
        """Persist one principal-owned transcript row and return a receipt."""
        from extensions import db

        try:
            parsed_session_id = uuid.UUID(str(session_id))
            parsed_run_id = uuid.UUID(str(run_id)) if run_id else None
        except (TypeError, ValueError, AttributeError):
            return ChatMessagePersistenceResult(
                ok=False,
                code="INVALID_CHAT_MESSAGE_CORRELATION",
                session_id=str(session_id) if session_id else None,
                run_id=str(run_id) if run_id else None,
            )

        if user_id is None or role not in {"user", "assistant", "system"}:
            return ChatMessagePersistenceResult(
                ok=False,
                code="INVALID_CHAT_MESSAGE",
                session_id=str(parsed_session_id),
                run_id=str(parsed_run_id) if parsed_run_id else None,
            )

        session = db.session.get(ChatSession, parsed_session_id)
        if session is None or int(session.user_id) != int(user_id):
            return ChatMessagePersistenceResult(
                ok=False,
                code="CHAT_SESSION_NOT_FOUND",
                session_id=str(parsed_session_id),
                run_id=str(parsed_run_id) if parsed_run_id else None,
            )

        try:
            msg = ChatMessage(
                session_id=session.id,
                role=role,
                content=content,
                run_id=parsed_run_id,
                is_enhanced=(role == "assistant"),
            )
            db.session.add(msg)

            session.updated_at = datetime.now(UTC)
            if not session.title and role == "user":
                bounded_title = content.strip()[:50]
                session.title = (
                    f"{bounded_title}..." if len(content.strip()) > 50 else bounded_title
                )

            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            logger.error(
                "Chat transcript persistence failed for session %s",
                parsed_session_id,
                exc_info=True,
            )
            return ChatMessagePersistenceResult(
                ok=False,
                code="CHAT_MESSAGE_PERSISTENCE_FAILED",
                session_id=str(parsed_session_id),
                run_id=str(parsed_run_id) if parsed_run_id else None,
            )

        rag_status = "not_applicable"
        if role in {"user", "assistant"}:
            rag_status = "synced"
            try:
                from backend.services.rag_service import get_rag_service

                rag = get_rag_service()
                rag.store_chat_message(
                    str(session.id),
                    str(msg.id),
                    role,
                    content,
                    user_id=str(user_id),
                )
            except Exception as exc:
                rag_status = "failed"
                logger.warning("Chat message RAG synchronization failed: %s", exc)

        return ChatMessagePersistenceResult(
            ok=True,
            code="CHAT_MESSAGE_PERSISTED",
            session_id=str(session.id),
            message_id=str(msg.id),
            run_id=str(parsed_run_id) if parsed_run_id else None,
            rag_status=rag_status,
        )

# Singleton instance
_gateway_instance = None

def get_gateway() -> LLMGateway:
    """Return the gateway owned by the active application instance."""
    try:
        from flask import current_app, has_app_context

        if has_app_context():
            gateway = current_app.extensions.get("dle_llm_gateway")
            if gateway is None:
                try:
                    from extensions import db
                    gateway = LLMGateway(db_session=db.session)
                except (ImportError, RuntimeError):
                    gateway = LLMGateway()
                current_app.extensions["dle_llm_gateway"] = gateway
            return gateway
    except ImportError:
        pass

    global _gateway_instance
    if _gateway_instance is None:
        try:
            from extensions import db
            _gateway_instance = LLMGateway(db_session=db.session)
        except (ImportError, RuntimeError):
            # Fallback for tests/environments without db
            _gateway_instance = LLMGateway()
    return _gateway_instance
