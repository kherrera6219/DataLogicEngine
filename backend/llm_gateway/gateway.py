# ruff: noqa: E402
"""Provider boundary and compatibility adapter for governed execution.

The backend-owned :class:`GovernedExecutionOrchestrator` is the only product
request pipeline. This module owns provider selection, bounded calls, usage, and
the legacy ``GatewayRequest``/``GatewayResponse`` transport adapter.
"""

import asyncio
import logging
import os
import sys
import uuid
from datetime import datetime, UTC, timedelta
from pathlib import Path
from typing import Any, AsyncIterator, Optional
from dataclasses import dataclass, field

# Add SDK to path
SDK_PATH = Path(__file__).resolve().parent.parent.parent / "sdk" / "UKG_Python_SDK"
if str(SDK_PATH) not in sys.path:
    sys.path.insert(0, str(SDK_PATH))

from models import LLMProvider, LLMProviderUsage, ChatSession, ChatMessage
from backend.utils.error_normalization import normalize_public_error_message
from backend.llm_gateway.governance import AIGovernanceEngine
from backend.llm_gateway.model_defaults import (
    ANTHROPIC_PRIMARY_MODEL,
    GOOGLE_FAST_MODEL,
    GOOGLE_PRIMARY_MODEL,
    OPENAI_FAST_MODEL,
    OPENAI_LONG_CONTEXT_MODEL,
    OPENAI_NANO_MODEL,
    OPENAI_PRO_MODEL,
    OPENAI_RESEARCH_MODEL,
    OPENAI_STANDARD_MODEL,
    default_model_for_provider,
)

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
        # Cloud-only: the app reaches its LLM over the network, so reachability is
        # simply whether a cloud provider (OpenAI / Google) is configured.
        state = "ONLINE" if providers else "OFFLINE"
        active_provider = providers[0] if providers else None
        cls._last_checked = now
        cls._last_result = {
            "state": state,
            "last_checked": now.isoformat(),
            "active_provider": active_provider,
            "details": {
                "configured_providers": providers,
                "ttl_seconds": cls._ttl_seconds,
            },
        }
        return dict(cls._last_result)

    @staticmethod
    def _configured_providers() -> list[str]:
        providers: list[str] = []
        env_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
            "azure": "AZURE_OPENAI_API_KEY",
        }
        for provider, env_name in env_map.items():
            if os.environ.get(env_name):
                providers.append(provider)

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
                    if provider_type and provider_type not in types:
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
        if request.model:
            return str(request.model)
        provider_type = str(getattr(provider_record, "provider_type", "") or "").lower()
        if provider_record and getattr(provider_record, "model_id", None):
            return str(provider_record.model_id)
        return default_model_for_provider(provider_type or None)

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

        # Unknown provider errors are treated as transient unless explicitly classified otherwise.
        return True

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
                # Intentional policy blocks (defense supervisor) — the user
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
        usage = dict(governed.usage or {})
        usage.setdefault("tokens_in", usage.get("prompt_tokens", 0))
        usage.setdefault("tokens_out", usage.get("completion_tokens", 0))
        return GatewayResponse(
            content=governed.answer,
            run_id=governed.trace_id,
            provider_used=governed.provider_used or "none",
            model_used=governed.model_used or request.model or "unknown",
            usage=usage,
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
        """
        Stream gateway responses as incremental chunks.

        This currently wraps the stable non-streaming execution path and emits
        chunked SSE-friendly payloads until native provider streaming is enabled.
        """
        response = await self.process(request)
        if not response.ok:
            yield {
                "type": "error",
                "error": response.error or "Gateway failed",
                "run_id": response.run_id,
                "provider_used": response.provider_used,
                "model_used": response.model_used,
            }
            return

        content = response.content or ""
        chunk_size = 256
        for index in range(0, len(content), chunk_size):
            await asyncio.sleep(0)
            yield {
                "type": "chunk",
                "index": index // chunk_size,
                "content": content[index:index + chunk_size],
                "run_id": response.run_id,
                "provider_used": response.provider_used,
                "model_used": response.model_used,
            }

        yield {
            "type": "done",
            "run_id": response.run_id,
            "provider_used": response.provider_used,
            "model_used": response.model_used,
            "usage": response.usage,
        }

    def _create_sdk_provider(self, provider_record: Optional[LLMProvider]) -> Any:
        """Create SDK provider instance from database config."""
        import os
        try:
            from ukg_sdk.providers import (
                OpenAIProvider,
                AzureOpenAIProvider,
                AnthropicProvider,
                GoogleGeminiProvider,
            )
        except ImportError:
            logger.warning("UKG SDK providers not available, using fallback")
            return None
        
        if not provider_record:
            # Fallback to environment
            return OpenAIProvider()
        
        # Try to get API key from database, fallback to environment
        api_key = None
        try:
            api_key = provider_record.get_api_key()
        except Exception as e:
            logger.warning(f"Failed to decrypt API key for {provider_record.name}: {e}")
        
        # Safety check for provider_type attribute
        raw_type = getattr(provider_record, 'provider_type', 'openai')
        provider_type = str(raw_type).lower() if raw_type else 'openai'
        
        # Fallback to environment variable if decryption failed
        if not api_key:
            env_key_map = {
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "azure": "AZURE_OPENAI_API_KEY",
                "google": "GOOGLE_API_KEY",
                "gemini": "GEMINI_API_KEY"
            }
            env_var = env_key_map.get(provider_type, f"{provider_type.upper()}_API_KEY")
            api_key = os.environ.get(env_var)
            
            # Special check for Gemini if Google key missing
            if provider_type == "google":
                api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            elif provider_type == "anthropic":
                # Backward compatibility for older .env naming
                api_key = api_key or os.getenv("anthropic_API_KEY")

            if api_key:
                logger.info(f"Using {env_var} environment variable for {provider_record.name}")
            else:
                logger.warning(f"No API key available for {provider_record.name}")
        
        if provider_type == "openai":
            return OpenAIProvider(api_key=api_key)
        elif provider_type == "azure":
            return AzureOpenAIProvider(
                api_key=api_key,
                endpoint=provider_record.endpoint,
                deployment=provider_record.deployment_name,
                api_version=provider_record.api_version,
            )
        elif provider_type == "anthropic":
            return AnthropicProvider(api_key=api_key)
        elif provider_type in ["google", "gemini"]:
             return GoogleGeminiProvider(api_key=api_key, model=provider_record.model_id or GOOGLE_PRIMARY_MODEL)
        else:
            # Default to OpenAI-compatible
            return OpenAIProvider(api_key=api_key, base_url=provider_record.endpoint)

    async def _get_eligible_providers(
        self,
        preferred_name: Optional[str] = None,
        meta: dict = None,
        allowed_provider_types: Optional[set[str]] = None,
        allowed_models: Optional[set[str]] = None,
    ) -> list[LLMProvider]:
        """Get list of active providers ordered by priority and task complexity."""
        import os
        meta = meta or {}
        task_tier = meta.get("tier", "high_stakes").lower()
        
        providers = []
        
        # Try to get providers from database.
        # Must push an app context because this async method may be called from
        # outside the Flask request lifecycle (Electron spawn, async coroutines).
        try:
            from flask import current_app as _cur_app
            _app = _cur_app._get_current_object()
        except RuntimeError:
            _app = None

        def _query_db():
            if preferred_name:
                q = LLMProvider.query.filter(
                    (LLMProvider.name == preferred_name) | (LLMProvider.provider_type == preferred_name),
                    LLMProvider.is_active
                )
                return q.all()
            else:
                return LLMProvider.query.filter_by(is_active=True).order_by(LLMProvider.priority).all()

        try:
            if _app is not None:
                with _app.app_context():
                    providers = _query_db()
            else:
                providers = _query_db()
        except Exception as e:
            logger.warning(f"Failed to query providers from DB: {e}")
            providers = []
        
        # Check for environment-based providers to fill missing types
        if True:
            # Create synthetic provider entries based on available API keys
            # Create synthetic provider entries based on available API keys

            # Helper class for synthetic providers
            class EnvProvider:
                def __init__(self, name, provider_type, priority=10, model=None):
                    self.id = name
                    self.name = name
                    self.provider_type = provider_type
                    self.endpoint = None
                    self.deployment_name = None
                    self.api_version = None
                    self.model_id = model or default_model_for_provider(provider_type)
                    self.priority = priority
                    self.timeout_seconds = self._env_timeout_default
                    self.max_retries = self._env_retry_default
                def get_api_key(self):
                    return None # _create_sdk_provider will fetch from env

                _env_timeout_default = LLMGateway._positive_int(
                    os.environ.get("LLM_PROVIDER_TIMEOUT_SECONDS"),
                    30,
                    minimum=1,
                    maximum=300,
                )
                _env_retry_default = LLMGateway._positive_int(
                    os.environ.get("LLM_PROVIDER_MAX_RETRIES"),
                    3,
                    minimum=1,
                    maximum=10,
                )
            
            # Logic (2026 Generation) - 3 Layer Redundancy
            # We need 3 slots: [Primary, Failover 1 (Cross-Provider), Failover 2 (Safety/Speed)]
            
            openai_key = os.environ.get("OPENAI_API_KEY")
            google_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
            anthropic_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("anthropic_API_KEY")
            openai_primary_model = os.environ.get("OPENAI_MODEL_PRIMARY", OPENAI_PRO_MODEL)
            openai_standard_model = os.environ.get("OPENAI_MODEL_STANDARD", OPENAI_STANDARD_MODEL)
            openai_fast_model = os.environ.get("OPENAI_MODEL_FAST", OPENAI_FAST_MODEL)
            openai_nano_model = os.environ.get("OPENAI_MODEL_NANO", OPENAI_NANO_MODEL)
            openai_long_context_model = os.environ.get("OPENAI_MODEL_LONG_CONTEXT", OPENAI_LONG_CONTEXT_MODEL)
            openai_research_model = os.environ.get("OPENAI_MODEL_RESEARCH", OPENAI_RESEARCH_MODEL)
            google_primary_model = os.environ.get("GOOGLE_MODEL_PRIMARY", GOOGLE_PRIMARY_MODEL)
            google_fast_model = os.environ.get("GOOGLE_MODEL_FAST", GOOGLE_FAST_MODEL)
            anthropic_primary_model = os.environ.get("ANTHROPIC_MODEL_PRIMARY", ANTHROPIC_PRIMARY_MODEL)

            providers_list = []

            # Helpers to add unique providers
            def add_provider(p_list, name, p_type, model, prio):
                # Simple check to avoid exact duplicates if logic overlaps
                for p in p_list:
                    if p.name == name:
                        return
                p_list.append(EnvProvider(name, p_type, priority=prio, model=model))

            # --- Construct 3-Layer List based on Tier ---
            
            if task_tier == "complex_reasoning":
                # Layer 1: Peak Intelligence (OpenAI)
                if openai_key:
                    add_provider(providers_list, "openai-primary", "openai", openai_primary_model, 1)
                # Layer 2: Cross-Provider Strong (Google)
                if google_key:
                    add_provider(providers_list, "google-fallback", "google", google_primary_model, 2)
                # Layer 3: Same-Provider Standard (OpenAI) or Other
                if openai_key:
                    add_provider(providers_list, "openai-safety", "openai", openai_standard_model, 3)
                elif google_key:
                    add_provider(providers_list, "google-safety", "google", google_fast_model, 3)

            elif task_tier == "security_defense":
                # High-Stakes Security Analysis routing
                # Layer 1: Best Reasoning Available (OpenAI)
                if openai_key:
                    add_provider(providers_list, "openai-defense", "openai", openai_primary_model, 1)
                # Layer 2: Strongest Alternate (Google)
                if google_key:
                    add_provider(providers_list, "google-defense", "google", google_primary_model, 2)
                # Layer 3: Fallback (OpenAI Standard)
                if openai_key:
                    add_provider(providers_list, "openai-defense-fallback", "openai", openai_standard_model, 3)

            elif task_tier == "deep_research":
                # Layer 1: Autonomous Research (OpenAI)
                if openai_key:
                    add_provider(providers_list, "openai-research", "openai", openai_research_model, 1)
                # Layer 2: Strong Reasoning (Google)
                if google_key:
                    add_provider(providers_list, "google-fallback", "google", google_primary_model, 2)
                # Layer 3: High Logic (OpenAI)
                if openai_key:
                    add_provider(providers_list, "openai-fallback", "openai", openai_primary_model, 3)

            elif task_tier in ["rag_heavy", "context_heavy"]:
                # Layer 1: Massive Context (Google)
                if google_key:
                    add_provider(providers_list, "google-context", "google", google_primary_model, 1)
                # Layer 2: Large Context Reliability (OpenAI)
                if openai_key:
                    add_provider(providers_list, "openai-fallback", "openai", openai_long_context_model, 2)
                # Layer 3: Speed/Capacity (Google)
                if google_key:
                    add_provider(providers_list, "google-flash", "google", google_fast_model, 3)

            elif task_tier in ["fast_chat", "structured_workflow"]:
                # Layer 1: Speed King (Google)
                if google_key:
                    add_provider(providers_list, "google-flash", "google", google_fast_model, 1)
                # Layer 2: Structured Efficient (OpenAI)
                if openai_key:
                    add_provider(providers_list, "openai-mini", "openai", openai_fast_model, 2)
                # Layer 3: Robust Fallback (Google)
                if google_key:
                    add_provider(providers_list, "google-std", "google", google_primary_model, 3)
                elif openai_key:
                    add_provider(providers_list, "openai-nano", "openai", openai_nano_model, 3)

            else:
                # Default / General Chat
                # Layer 1: Balanced (OpenAI)
                if openai_key:
                    add_provider(providers_list, "openai-default", "openai", openai_standard_model, 1)
                # Layer 2: Balanced (Google)
                if google_key:
                    add_provider(providers_list, "google-default", "google", google_primary_model, 2)
                # Layer 3: Speed (Google)
                if google_key:
                    add_provider(providers_list, "google-speed", "google", google_fast_model, 3)
            
            # If we still have space and Anthropic key exists, inject it as ultimate backup
            if anthropic_key and len(providers_list) < 3:
                add_provider(providers_list, "anthropic-backup", "anthropic", anthropic_primary_model, 4)

            preferred_env_provider = LLMGateway._preferred_env_provider()

            if providers_list:
                # Sort by configured env preference, then by tier priority.
                providers_list.sort(key=LLMGateway._env_provider_sort_key)
                logger.info(
                    "Generated %s environment-based providers for tier '%s': %s",
                    len(providers_list),
                    task_tier,
                    [p.name for p in providers_list],
                )
                db_types = {str(getattr(p, "provider_type", "")).strip().lower() for p in providers}
                added_types = set()
                for p in providers_list:
                    if p.provider_type not in db_types and p.provider_type not in added_types:
                        providers.append(p)
                        added_types.add(p.provider_type)

            if preferred_env_provider and not preferred_name:
                # A desktop env default is explicit operator intent. Do not
                # silently fall back to saved legacy/local providers such as
                # Ollama after the configured cloud provider fails.
                allowed_env_types = {preferred_env_provider}
                if preferred_env_provider == "google":
                    allowed_env_types.add("gemini")
                providers = [
                    provider
                    for provider in providers
                    if str(getattr(provider, "provider_type", "") or "").strip().lower() in allowed_env_types
                ]

            providers.sort(key=LLMGateway._env_provider_sort_key)

        if allowed_provider_types:
            providers = [
                provider
                for provider in providers
                if self._provider_matches_policy(provider, allowed_provider_types)
            ]

        if allowed_models:
            filtered_by_model: list[LLMProvider] = []
            for provider in providers:
                provider_model = str(getattr(provider, "model_id", "") or "").strip().lower()
                if not provider_model or provider_model in allowed_models:
                    filtered_by_model.append(provider)
            providers = filtered_by_model

        return providers

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
            return {
                "ok": True,
                "answer": response.text,
                "usage": response.usage or {},
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    async def _record_usage(
        self,
        provider_id: Optional[uuid.UUID],
        user_id: Optional[int],
        api_key_id: Optional[str],
        run_id: str,
        model: Optional[str],
        tokens_in: int,
        tokens_out: int,
        latency_ms: int,
        success: bool,
        estimated_cost_usd: Optional[float] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Record usage for analytics."""
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
            if provider_uuid is None:
                logger.debug("Skipping usage persistence for non-DB provider id: %s", provider_id)
                return

            usage_payload = {
                "provider_id": provider_uuid,
                "user_id": user_id,
                "api_key_id": _parse_uuid(api_key_id),
                "run_id": _parse_uuid(run_id),
                "model": model,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "latency_ms": latency_ms,
                "success": success,
            }

            if hasattr(LLMProviderUsage, "estimated_cost_usd") and estimated_cost_usd is not None:
                usage_payload["estimated_cost_usd"] = float(estimated_cost_usd)

            if hasattr(LLMProviderUsage, "error_code") and error_code:
                usage_payload["error_code"] = error_code
            if hasattr(LLMProviderUsage, "error_message") and error_message:
                usage_payload["error_message"] = error_message

            db.session.add(LLMProviderUsage(**usage_payload))
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                if "error_code" in usage_payload or "error_message" in usage_payload:
                    usage_payload.pop("error_code", None)
                    usage_payload.pop("error_message", None)
                    db.session.add(LLMProviderUsage(**usage_payload))
                    db.session.commit()
                else:
                    raise

            if provider_uuid:
                provider = LLMProvider.query.get(provider_uuid)
                if provider:
                    provider.last_used_at = datetime.now(UTC)
                    db.session.commit()
                    
        except Exception as e:
            logger.error(f"Failed to record usage: {e}")
    
    async def close(self) -> None:
        """Clean up."""
        self._overlays.clear()

    async def _save_chat_message(self, session_id: str, user_id: Optional[int], role: str, content: str, run_id: Optional[str] = None) -> None:
        """Persist message to SQL database and update session."""
        try:
            from extensions import db
            import uuid
            
            # 1. Ensure Session exists
            session = ChatSession.query.get(uuid.UUID(session_id))
            if not session:
                # Fallback: if we don't have a user_id, we can't create a session properly 
                # but we'll try to find the current user if possible or just skip
                if not user_id:
                    return
                
                session = ChatSession(
                    id=uuid.UUID(session_id),
                    user_id=user_id,
                    title=content[:50] + "..." if role == "user" else "New Chat"
                )
                db.session.add(session)
            
            # 2. Add Message
            msg = ChatMessage(
                session_id=session.id,
                role=role,
                content=content,
                run_id=uuid.UUID(run_id) if run_id else None,
                is_enhanced=(role == "assistant")
            )
            db.session.add(msg)
            
            # 3. Update session timestamp and title if it's the first message
            session.updated_at = datetime.now(UTC)
            if not session.title and role == "user":
                session.title = content[:50] + "..."
                
            db.session.commit()
            
            # 4. Optional: Sync to RAG for semantic search
            if role in ["user", "assistant"]:
                try:
                    from backend.services.rag_service import get_rag_service
                    rag = get_rag_service()
                    rag.store_chat_message(
                        str(session.id),
                        str(msg.id),
                        role,
                        content,
                        user_id=str(user_id) if user_id else None,
                    )
                except Exception as e:
                    logger.warning(f"Failed to sync message to RAG: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to save chat message: {e}")

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
