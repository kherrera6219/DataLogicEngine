# ruff: noqa: E402
"""
LLM Gateway Core - Integrated with UKG SDK

Routes LLM requests through the UKG reasoning pipeline using the
existing UKG_Python_SDK (UKGOverlay, CoordinateResolver17, KAExecutor).

The gateway provides:
- Database-stored provider configs with encrypted API keys
- External API key management for customers
- Usage analytics
- REST wrapper around the SDK
"""

import asyncio
import inspect
import logging
import os
import socket
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

from models import LLMProvider, LLMProviderUsage, ChatSession, ChatMessage, UserAIPreferences
from backend.utils.error_normalization import normalize_public_error_message
from backend.llm_gateway.governance import AIGovernanceEngine
from backend.llm_gateway.latency_metrics import record_ai_request
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
    coordinate: Optional[str] = None
    tier: Optional[str] = None
    layers: Optional[list[str]] = None
    trace: Optional[list[dict]] = None
    explainability: Optional[dict] = None
    warnings: list[str] = field(default_factory=list)
    error: Optional[str] = None
    # Escalation tier metadata (Sprint 6b) — set by ComplexityClassifier.
    escalation_tier: Optional[int] = None
    escalation_reason: Optional[str] = None
    escalation_label: Optional[str] = None
    # Acceleration metadata — populated when Local Model Acceleration is active.
    meta: dict[str, Any] = field(default_factory=dict)


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
        local_available = cls._tcp_reachable("127.0.0.1", int(os.environ.get("OLLAMA_PORT", "11434")))
        remote_configured = any(provider not in {"local_slm", "ollama", "vllm"} for provider in providers)
        state = "ONLINE" if remote_configured or local_available else "OFFLINE"
        if remote_configured and not local_available and os.environ.get("IS_DESKTOP_APP", "false").lower() in {"1", "true", "yes", "on"}:
            state = "DEGRADED"

        active_provider = "local_slm" if local_available else (providers[0] if providers else None)
        cls._last_checked = now
        cls._last_result = {
            "state": state,
            "last_checked": now.isoformat(),
            "active_provider": active_provider,
            "details": {
                "configured_providers": providers,
                "local_model_available": local_available,
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

        if os.environ.get("LOCAL_SLM_ENDPOINT") or os.environ.get("OLLAMA_BASE_URL"):
            providers.append("local_slm")
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

    @staticmethod
    def _tcp_reachable(host: str, port: int) -> bool:
        try:
            with socket.create_connection((host, port), timeout=0.25):
                return True
        except OSError:
            return False


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
    def _dmrf_enabled(meta: dict[str, Any]) -> bool:
        """Return True when DMRF should wrap the gateway control plane."""
        if meta.get("use_dmrf") is not None:
            return str(meta.get("use_dmrf")).lower() in {"1", "true", "yes", "on"}
        return os.environ.get("USE_DMRF", "false").lower() in {"1", "true", "yes", "on"}

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
        # For local providers the escalation engine may have selected a model
        # that differs from the DB-stored default (e.g. Tier 0 vs Tier 1).
        provider_type = str(getattr(provider_record, "provider_type", "") or "").lower()
        if provider_type in {"ollama", "local_slm", "vllm"}:
            override = request.meta.get("ollama_model_override")
            if override:
                return str(override)
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
    
    async def process(self, request: GatewayRequest) -> GatewayResponse:
        """
        Process a gateway request with failover and circuit breaker.
        """
        run_id = str(uuid.uuid4())
        request.meta["run_id"] = run_id
        start_time = datetime.now(UTC)

        query = self._extract_query(request.messages)
        governance = self._governance.prepare_request(request, query)
        if not governance.ok:
            self._governance.record_audit_event(
                run_id=run_id,
                user_id=request.user_id,
                api_key_id=request.api_key_id,
                provider=request.provider,
                model=request.model or "unknown",
                model_version="unknown",
                governance_flags=governance.governance_flags,
                request_tokens_estimate=governance.estimated_request_tokens,
                success=False,
                error_code="GOVERNANCE_BLOCK",
                error_message=governance.error,
                metadata={"timestamp": datetime.now(UTC).isoformat()},
            )
            return self._error_response(
                run_id,
                governance.error or "Request blocked by governance policy",
                start_time,
                request,
            )

        query = governance.query
        request.meta["governance_flags"] = governance.governance_flags
        if governance.prompt_template_key:
            request.meta["prompt_template_key"] = governance.prompt_template_key
            request.meta["prompt_template_version"] = governance.prompt_template_version
        if governance.routing_policy_name:
            request.meta["routing_policy_name"] = governance.routing_policy_name
            request.meta["routing_policy_version"] = governance.routing_policy_version
        request.meta["estimated_request_tokens"] = governance.estimated_request_tokens

        allowed_provider_types = self._normalize_allowlist(
            request.meta.get("allowed_provider_types") or request.meta.get("allowed_providers")
        )
        allowed_models = self._normalize_allowlist(request.meta.get("allowed_models"))

        if governance.allowed_provider_types:
            allowed_provider_types = (
                allowed_provider_types & governance.allowed_provider_types
                if allowed_provider_types
                else set(governance.allowed_provider_types)
            )
        if governance.allowed_models:
            allowed_models = (
                allowed_models & governance.allowed_models
                if allowed_models
                else set(governance.allowed_models)
            )

        if allowed_provider_types:
            request.meta["allowed_provider_types"] = sorted(allowed_provider_types)
        if allowed_models:
            request.meta["allowed_models"] = sorted(allowed_models)

        if request.run_ukg_pipeline and self._dmrf_enabled(request.meta):
            try:
                from backend.dmrf import DMRFOrchestrator

                dmrf_result = await DMRFOrchestrator(
                    desktop_mode=self._desktop_local_first_enabled(),
                    db_session=self.db,
                ).process(
                    query,
                    context=request.meta,
                    offline=bool(request.meta.get("offline") or request.meta.get("providers_unreachable")),
                )
                dmrf_bundle = dmrf_result.export_bundle()
                request.meta["dmrf"] = dmrf_bundle
                request.meta["dmrf_tier"] = dmrf_result.tier
                request.meta["axis_vector"] = dmrf_bundle.get("axis_vector", {})
                if not dmrf_result.ok:
                    return self._error_response(
                        run_id,
                        "; ".join(dmrf_result.warnings) or "DMRF blocked request",
                        start_time,
                        request,
                    )
            except Exception as exc:
                logger.warning("DMRF control plane failed open: %s", exc)
                request.meta.setdefault("dmrf_warnings", []).append(str(exc))

        requested_model = str(request.model).strip().lower() if request.model else ""
        if allowed_models and requested_model and requested_model not in allowed_models:
            self._governance.record_audit_event(
                run_id=run_id,
                user_id=request.user_id,
                api_key_id=request.api_key_id,
                provider=request.provider,
                model=request.model or "unknown",
                model_version="unknown",
                prompt_template_key=request.meta.get("prompt_template_key"),
                prompt_template_version=request.meta.get("prompt_template_version"),
                routing_policy_name=request.meta.get("routing_policy_name"),
                routing_policy_version=request.meta.get("routing_policy_version"),
                governance_flags=request.meta.get("governance_flags"),
                request_tokens_estimate=request.meta.get("estimated_request_tokens"),
                success=False,
                error_code="MODEL_ALLOWLIST_BLOCK",
                error_message=f"Requested model '{request.model}' is not allowed by policy",
                metadata={"timestamp": datetime.now(UTC).isoformat()},
            )
            return self._error_response(
                run_id,
                f"Requested model '{request.model}' is not allowed by API key policy",
                start_time,
                request,
            )
        
        # Apply user AI preferences (disable check + preferred provider)
        _store_history = True
        if request.user_id:
            try:
                user_prefs = UserAIPreferences.query.filter_by(user_id=request.user_id).first()
                if user_prefs:
                    if not user_prefs.ai_processing_enabled:
                        return self._error_response(
                            run_id, "AI processing is disabled in your account settings.", start_time, request
                        )
                    if not request.provider and user_prefs.preferred_provider:
                        request.provider = user_prefs.preferred_provider
                    if not request.model and user_prefs.preferred_model:
                        request.model = user_prefs.preferred_model
                    _store_history = bool(user_prefs.store_chat_history)
            except Exception:
                pass  # Preferences are optional — never block a request on DB failure

        # ── Escalation tier classification (Sprint 6b/6c) ───────────────────
        # Select the optimal model tier for this query via heuristic scoring.
        # Runs only when the caller has not pinned a specific provider or model,
        # AND user preferences have not set one.
        #
        # Cloud escalation (T4 = Gemini Flash 3.5, T5 = GPT-5.5) is unlocked
        # automatically when the user has saved at least one active Google or
        # OpenAI provider record in Settings.  No manual flag required.
        if not request.provider and not request.model:
            try:
                from backend.llm_gateway.complexity_classifier import ComplexityClassifier
                from backend.llm_gateway.escalation_config import get_tier_config
                from backend.llm_gateway.tier_availability import find_best_available_tier
                allow_cloud = self._has_active_cloud_providers()
                clf_result = ComplexityClassifier().classify(
                    query, allow_cloud_escalation=allow_cloud
                )
                # Graceful cascade: if the classified tier's model isn't pulled,
                # fall back to the best available tier rather than failing.
                effective_tier = find_best_available_tier(
                    clf_result.tier, allow_cloud=allow_cloud
                )
                tier_cfg = get_tier_config(effective_tier)
                if tier_cfg:
                    request.meta["escalation_tier"] = effective_tier
                    request.meta["escalation_reason"] = clf_result.reason
                    request.meta["escalation_label"] = tier_cfg.label
                    if tier_cfg.is_cloud:
                        # Redirect routing to the cloud provider for this tier.
                        request.provider = tier_cfg.provider_type
                        request.model = tier_cfg.model
                    else:
                        # Local tier — keep Ollama routing, override the model string.
                        request.meta["ollama_model_override"] = tier_cfg.model
                    logger.info(
                        "Escalation → tier=%s model=%s reason=%s cloud_allowed=%s"
                        "%s",
                        effective_tier,
                        tier_cfg.model,
                        clf_result.reason,
                        allow_cloud,
                        f" (cascaded from T{clf_result.tier})"
                        if effective_tier != clf_result.tier else "",
                    )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Escalation classifier failed open: %s", exc)

        # ── Defense supervisor (N2) ─────────────────────────────────────────
        # LLM-backed semantic screening on the local model for pipeline
        # queries. Complements the pattern shields already applied in
        # governance.prepare_request; fail-open when no local model exists.
        supervisor_block = self._screen_with_defense_supervisor(request, query)
        if supervisor_block:
            verdict = request.meta.get("defense_supervisor", {})
            self._governance.record_audit_event(
                run_id=run_id,
                user_id=request.user_id,
                api_key_id=request.api_key_id,
                provider=request.provider,
                model=request.model or "unknown",
                model_version="unknown",
                governance_flags=(request.meta.get("governance_flags") or [])
                + ["defense_supervisor_blocked"],
                request_tokens_estimate=request.meta.get("estimated_request_tokens"),
                success=False,
                error_code="DEFENSE_SUPERVISOR_BLOCK",
                error_message=supervisor_block,
                metadata={
                    "timestamp": datetime.now(UTC).isoformat(),
                    "threat_type": verdict.get("threat_type"),
                    "threat_score": verdict.get("threat_score"),
                    "recommended_action": verdict.get("recommended_action"),
                },
            )
            return self._error_response(
                run_id,
                "Request blocked by security policy",
                start_time,
                request,
            )

        # 1. Get eligible providers
        providers = await self._get_eligible_providers(
            request.provider,
            request.meta,
            allowed_provider_types=allowed_provider_types or None,
            allowed_models=allowed_models or None,
        )
        if not providers:
            self._governance.record_audit_event(
                run_id=run_id,
                user_id=request.user_id,
                api_key_id=request.api_key_id,
                provider=request.provider,
                model=request.model or "unknown",
                model_version="unknown",
                prompt_template_key=request.meta.get("prompt_template_key"),
                prompt_template_version=request.meta.get("prompt_template_version"),
                routing_policy_name=request.meta.get("routing_policy_name"),
                routing_policy_version=request.meta.get("routing_policy_version"),
                governance_flags=request.meta.get("governance_flags"),
                request_tokens_estimate=request.meta.get("estimated_request_tokens"),
                success=False,
                error_code="NO_PROVIDER",
                error_message="No active providers found",
                metadata={"timestamp": datetime.now(UTC).isoformat()},
            )
            return self._error_response(run_id, "No active providers found", start_time, request)

        last_error = None

        messages_for_request = self._replace_latest_user_message(request.messages, query)
        user_id_str = str(request.user_id) if request.user_id else "anonymous"
        
        history = []
        if request.session_id:
            if _store_history:
                await self._save_chat_message(request.session_id, request.user_id, "user", query)
            history = await self._get_recent_history(request.session_id)
        
        # 3. Try providers in order
        for provider_record in providers:
            cb = self._get_circuit_breaker(str(provider_record.id))
            
            if not cb.can_execute():
                logger.warning(f"Circuit OPEN for provider {provider_record.name}, skipping...")
                continue

            model = self._resolve_model(request, provider_record)
            if allowed_models and model.strip().lower() not in allowed_models:
                logger.warning(
                    "Skipping provider %s due to API key model policy",
                    getattr(provider_record, "name", "unknown"),
                )
                continue
            
            provider_timeout_seconds = self._provider_timeout_seconds(provider_record)
            max_retries = self._provider_max_retries(provider_record)
            for attempt in range(max_retries):
                try:
                    # 4. Create SDK provider and run
                    sdk_provider = self._create_sdk_provider(provider_record)
                    
                    full_messages = history + messages_for_request
                    
                    # RAG context captured here for the exact-cache key (see Local Model
                    # Acceleration).  Must be set *before* the if/else so it is always
                    # in scope, even for direct (non-UKG) calls where RAG is not used.
                    _rag_ctx_for_cache = ""

                    if request.run_ukg_pipeline:
                        # Retrieve relevant context from RAG (VectorStore)
                        rag_context = ""
                        if request.meta.get("use_rag", True):
                            try:
                                from backend.services.rag_service import get_rag_service
                                rag = get_rag_service()
                                rag_chunks = []

                                doc_context = rag.get_context_for_query(query, max_tokens=1200)
                                if doc_context:
                                    rag_chunks.append(doc_context)

                                # Add semantic memory from prior chat sessions for this user.
                                if request.user_id:
                                    prior_hits = rag.search_user_chat_history(
                                        user_id=str(request.user_id),
                                        query=query,
                                        k=6,
                                        exclude_session_id=request.session_id,
                                    )
                                    if prior_hits:
                                        memory_lines = []
                                        for hit in prior_hits[:3]:
                                            role = hit.get("metadata", {}).get("role", "message")
                                            text = (hit.get("text") or "").strip()
                                            if not text:
                                                continue
                                            clipped = text[:280] + ("..." if len(text) > 280 else "")
                                            memory_lines.append(f"{role}: {clipped}")
                                        if memory_lines:
                                            rag_chunks.append(
                                                "Relevant context from prior chat threads:\n" + "\n".join(memory_lines)
                                            )

                                rag_context = "\n\n---\n\n".join(rag_chunks)
                                if rag_context:
                                    logger.debug(f"Retrieved RAG context: {len(rag_context)} chars")
                            except Exception as e:
                                logger.warning(f"RAG context retrieval failed: {e}")
                        
                        # Capture RAG context for Local Model Acceleration cache key.
                        _rag_ctx_for_cache = rag_context

                        # Inject RAG context into meta for UKG overlay
                        augmented_meta = {**request.meta, "rag_context": rag_context, "chat_history": history}
                        
                        # Decide between standard overlay and quad persona analysis
                        if request.mode == "quad" or request.meta.get("quad_persona", False):
                            result_coro = self._run_quad_analysis(
                                query=query,
                                context=augmented_meta,
                            )
                        else:
                            result_coro = self._run_ukg_overlay(
                                sdk_provider=sdk_provider,
                                model=model,
                                query=query,
                                run_id=run_id,
                                user_id=user_id_str,
                                session_id=request.session_id,
                                meta=augmented_meta,
                                temperature=request.temperature,
                                max_tokens=request.max_tokens or 1024,
                            )
                    else:
                        result_coro = self._direct_llm_call(
                            sdk_provider=sdk_provider,
                            model=model,
                            messages=full_messages,
                            temperature=request.temperature,
                            max_tokens=request.max_tokens or 1024,
                        )

                    # ------------------------------------------------------------------
                    # Local Model Acceleration: keep-alive + exact response cache.
                    # Applies only to local providers (ollama / local_slm / vllm).
                    # Fail-open: exceptions raised before the model call starts fall
                    # through to the bare await below; exceptions after the model
                    # call started (e.g. timeout) propagate to provider failover.
                    # ------------------------------------------------------------------
                    _local_provider_types = {"ollama", "local_slm", "vllm"}
                    _provider_type = str(
                        getattr(provider_record, "provider_type", "") or ""
                    ).lower()

                    if _provider_type in _local_provider_types:
                        try:
                            from backend.local_model_acceleration import (
                                get_local_model_acceleration_manager,
                            )
                            _accel = get_local_model_acceleration_manager()
                            _accel.start_keepalive(model, _provider_type)

                            # Capture result_coro in a closure so it is awaited
                            # exactly once inside generate_with_cache on cache miss.
                            _captured_coro = result_coro

                            async def _call_model() -> dict:
                                return await asyncio.wait_for(
                                    _captured_coro,
                                    timeout=provider_timeout_seconds,
                                )

                            result = await _accel.generate_with_cache(
                                provider_type=_provider_type,
                                model_name=model,
                                task_type=(
                                    request.meta.get("task_type")
                                    or request.mode
                                    or "gateway_chat"
                                ),
                                prompt=query,
                                rag_context=_rag_ctx_for_cache,
                                system=None,
                                options={
                                    "temperature": request.temperature,
                                    "max_tokens": request.max_tokens or 1024,
                                    "run_ukg_pipeline": request.run_ukg_pipeline,
                                    "mode": request.mode,
                                },
                                metadata=request.meta,
                                call_model=_call_model,
                            )
                            # Hoist acceleration metadata into request.meta so
                            # _build_response can pass it through to the API response.
                            _accel_meta = result.pop("_acceleration", None)
                            if _accel_meta:
                                request.meta["local_model_acceleration"] = _accel_meta
                            # On a cache hit the captured pipeline coroutine was
                            # never started; close it so GC does not emit
                            # "coroutine was never awaited".
                            if inspect.getcoroutinestate(result_coro) == inspect.CORO_CREATED:
                                result_coro.close()
                        except Exception as _accel_exc:  # noqa: BLE001
                            # Fail-open only while the pipeline coroutine is still
                            # unstarted. If generate_with_cache already awaited it,
                            # re-awaiting would raise RuntimeError and the model
                            # call may have had side effects — propagate instead.
                            if inspect.getcoroutinestate(result_coro) != inspect.CORO_CREATED:
                                raise
                            logger.warning(
                                "Local model acceleration failed open — "
                                "falling back to direct call: %s",
                                _accel_exc,
                            )
                            result = await asyncio.wait_for(
                                result_coro, timeout=provider_timeout_seconds
                            )
                    else:
                        result = await asyncio.wait_for(
                            result_coro, timeout=provider_timeout_seconds
                        )

                    if result.get("ok", True):
                        cb.record_success()
                        latency_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
                        record_ai_request(
                            provider=getattr(provider_record, "provider_type", "unknown"),
                            duration_ms=latency_ms,
                            success=True,
                        )

                        usage_payload = result.get("usage", {}) if isinstance(result.get("usage"), dict) else {}
                        tokens_in = int(usage_payload.get("prompt_tokens", 0) or 0)
                        tokens_out = int(usage_payload.get("completion_tokens", 0) or 0)
                        estimated_cost_usd = self._governance.estimate_cost_usd(model, tokens_in, tokens_out)
                        usage_payload["estimated_cost_usd"] = estimated_cost_usd
                        result["usage"] = usage_payload

                        moderated_answer, output_classification, governance_warnings = (
                            self._governance.apply_output_controls(result.get("answer", ""))
                        )
                        result["answer"] = moderated_answer
                        explainability = result.get("explainability")
                        if not isinstance(explainability, dict):
                            explainability = {}
                        explainability["output_classification"] = output_classification
                        result["explainability"] = explainability
                        result["warnings"] = list(result.get("warnings", [])) + governance_warnings

                        await self._record_usage(
                            provider_record.id,
                            request.user_id,
                            request.api_key_id,
                            run_id,
                            model,
                            tokens_in,
                            tokens_out,
                            latency_ms,
                            True,
                            estimated_cost_usd=estimated_cost_usd,
                        )

                        model_version = (
                            result.get("model_version")
                            or (result.get("metadata", {}) or {}).get("model_version")
                            or getattr(provider_record, "api_version", None)
                            or "unknown"
                        )
                        self._governance.record_audit_event(
                            run_id=run_id,
                            user_id=request.user_id,
                            api_key_id=request.api_key_id,
                            provider=getattr(provider_record, "provider_type", "unknown"),
                            model=model,
                            model_version=model_version,
                            prompt_template_key=request.meta.get("prompt_template_key"),
                            prompt_template_version=request.meta.get("prompt_template_version"),
                            routing_policy_name=request.meta.get("routing_policy_name"),
                            routing_policy_version=request.meta.get("routing_policy_version"),
                            classification=output_classification,
                            governance_flags=request.meta.get("governance_flags"),
                            request_tokens_estimate=request.meta.get("estimated_request_tokens"),
                            tokens_in=tokens_in,
                            tokens_out=tokens_out,
                            estimated_cost_usd=estimated_cost_usd,
                            success=True,
                            metadata={
                                "timestamp": datetime.now(UTC).isoformat(),
                                "original_run_id": request.meta.get("local_model_acceleration", {}).get("original_run_id")
                            },
                        )
                        
                        if request.session_id and _store_history:
                            await self._save_chat_message(request.session_id, request.user_id, "assistant", result.get("answer", ""), run_id)
                        
                        # If Tier 2+ and it was a cache hit, record a compliance cache hit audit event
                        _accel_meta = request.meta.get("local_model_acceleration", {})
                        if _accel_meta.get("cache_hit"):
                            tier = result.get("tier") or request.meta.get("escalation_tier")
                            _tier_exclusions = {"", "0", "t0", "1", "t1", "trivial"}
                            if tier and str(tier).lower().strip() not in _tier_exclusions:
                                try:
                                    from backend.truth_engine.truth_memory.manager import TruthMemoryManager
                                    memory_mgr = TruthMemoryManager(db_session=self.db)
                                    memory_mgr.audit_logger.log_event(
                                        session_id=request.session_id or f"session_{uuid.uuid4().hex[:12]}",
                                        event_type="cache_hit",
                                        event_data={
                                            "run_id": run_id,
                                            "original_run_id": _accel_meta.get("original_run_id"),
                                            "query": query,
                                            "model": model,
                                            "tier": str(tier),
                                        },
                                        category="compliance"
                                    )
                                except Exception as audit_exc:
                                    logger.warning("Failed to record cache hit audit event: %s", audit_exc)
                                              
                        return self._build_response(
                            result, run_id, provider_record, model, latency_ms,
                            escalation_meta=request.meta,
                        )
                    
                    # If provider returned !ok but might be retryable (e.g., 503)
                    last_error = result.get("error", "Unknown provider error")
                    is_rate_limited = self._is_rate_limit_error(last_error)
                    # Rate-limit (429) is NOT retried — the window won't reset in ms —
                    # and does NOT count as a circuit-breaker failure.
                    retryable = not is_rate_limited and (
                        bool(result.get("retryable")) or self._is_retryable_error(last_error)
                    )
                    logger.warning(
                        "Provider %s attempt %s/%s failed: %s (retryable=%s, rate_limited=%s)",
                        provider_record.name,
                        attempt + 1,
                        max_retries,
                        last_error,
                        retryable,
                        is_rate_limited,
                    )

                    if attempt < max_retries - 1 and retryable:
                        await self._retry_backoff_sleep(attempt)
                        continue

                    if not is_rate_limited:
                        cb.record_failure()
                    latency_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
                    record_ai_request(
                        provider=getattr(provider_record, "provider_type", "unknown"),
                        duration_ms=latency_ms,
                        success=False,
                    )
                    await self._record_usage(
                        provider_record.id,
                        request.user_id,
                        request.api_key_id,
                        run_id,
                        model,
                        result.get("usage", {}).get("prompt_tokens", 0),
                        result.get("usage", {}).get("completion_tokens", 0),
                        latency_ms,
                        False,
                        error_code="PROVIDER_ERROR",
                        error_message=last_error,
                    )
                    self._governance.record_audit_event(
                        run_id=run_id,
                        user_id=request.user_id,
                        api_key_id=request.api_key_id,
                        provider=getattr(provider_record, "provider_type", "unknown"),
                        model=model,
                        model_version=getattr(provider_record, "api_version", None) or "unknown",
                        prompt_template_key=request.meta.get("prompt_template_key"),
                        prompt_template_version=request.meta.get("prompt_template_version"),
                        routing_policy_name=request.meta.get("routing_policy_name"),
                        routing_policy_version=request.meta.get("routing_policy_version"),
                        governance_flags=request.meta.get("governance_flags"),
                        request_tokens_estimate=request.meta.get("estimated_request_tokens"),
                        success=False,
                        error_code="PROVIDER_ERROR",
                        error_message=last_error,
                        metadata={"timestamp": datetime.now(UTC).isoformat()},
                    )
                    break  # Try next provider

                except asyncio.TimeoutError:
                    last_error = f"Provider request timed out after {provider_timeout_seconds}s"
                    logger.warning(
                        "Provider %s attempt %s/%s timed out after %ss",
                        provider_record.name,
                        attempt + 1,
                        max_retries,
                        provider_timeout_seconds,
                    )
                    if attempt < max_retries - 1:
                        await self._retry_backoff_sleep(attempt)
                        continue

                    cb.record_failure()
                    latency_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
                    record_ai_request(
                        provider=getattr(provider_record, "provider_type", "unknown"),
                        duration_ms=latency_ms,
                        success=False,
                    )
                    await self._record_usage(
                        provider_record.id,
                        request.user_id,
                        request.api_key_id,
                        run_id,
                        model,
                        0,
                        0,
                        latency_ms,
                        False,
                        error_code="TIMEOUT",
                        error_message=last_error,
                    )
                    self._governance.record_audit_event(
                        run_id=run_id,
                        user_id=request.user_id,
                        api_key_id=request.api_key_id,
                        provider=getattr(provider_record, "provider_type", "unknown"),
                        model=model,
                        model_version=getattr(provider_record, "api_version", None) or "unknown",
                        prompt_template_key=request.meta.get("prompt_template_key"),
                        prompt_template_version=request.meta.get("prompt_template_version"),
                        routing_policy_name=request.meta.get("routing_policy_name"),
                        routing_policy_version=request.meta.get("routing_policy_version"),
                        governance_flags=request.meta.get("governance_flags"),
                        request_tokens_estimate=request.meta.get("estimated_request_tokens"),
                        success=False,
                        error_code="TIMEOUT",
                        error_message=last_error,
                        metadata={"timestamp": datetime.now(UTC).isoformat()},
                    )
                    break  # Try next provider

                except Exception as e:
                    last_error = str(e)
                    is_rate_limited = self._is_rate_limit_error(last_error)
                    retryable = not is_rate_limited and self._is_retryable_error(last_error)
                    logger.error(
                        "Provider %s attempt %s/%s exception: %s (retryable=%s, rate_limited=%s)",
                        provider_record.name,
                        attempt + 1,
                        max_retries,
                        e,
                        retryable,
                        is_rate_limited,
                        exc_info=True,
                    )
                    if attempt < max_retries - 1 and retryable:
                        await self._retry_backoff_sleep(attempt)
                        continue

                    if not is_rate_limited:
                        cb.record_failure()
                    latency_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
                    record_ai_request(
                        provider=getattr(provider_record, "provider_type", "unknown"),
                        duration_ms=latency_ms,
                        success=False,
                    )
                    await self._record_usage(
                        provider_record.id,
                        request.user_id,
                        request.api_key_id,
                        run_id,
                        model,
                        0,
                        0,
                        latency_ms,
                        False,
                        error_code="EXCEPTION",
                        error_message=last_error,
                    )
                    self._governance.record_audit_event(
                        run_id=run_id,
                        user_id=request.user_id,
                        api_key_id=request.api_key_id,
                        provider=getattr(provider_record, "provider_type", "unknown"),
                        model=model,
                        model_version=getattr(provider_record, "api_version", None) or "unknown",
                        prompt_template_key=request.meta.get("prompt_template_key"),
                        prompt_template_version=request.meta.get("prompt_template_version"),
                        routing_policy_name=request.meta.get("routing_policy_name"),
                        routing_policy_version=request.meta.get("routing_policy_version"),
                        governance_flags=request.meta.get("governance_flags"),
                        request_tokens_estimate=request.meta.get("estimated_request_tokens"),
                        success=False,
                        error_code="EXCEPTION",
                        error_message=last_error,
                        metadata={"timestamp": datetime.now(UTC).isoformat()},
                    )
                    break  # Try next provider

        # All eligible providers failed or were unavailable.
        return self._error_response(
            run_id,
            last_error or "All providers failed to generate a response",
            start_time,
            request,
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
                LocalSLMProvider,
                GoogleGeminiProvider,
                OllamaProvider,
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
        elif provider_type == "ollama":
            # OllamaProvider: strips /v1 suffix if stored URL includes it, so the
            # same base URL works whether the user typed the bare host or the /v1 path.
            return OllamaProvider(
                base_url=provider_record.endpoint or "http://localhost:11434"
            )
        elif provider_type in ["local_slm", "vllm"]:
            # LocalSLMProvider: generic OpenAI-compat backend (vLLM, LM Studio, etc.)
            # that does not expose /api/tags — keep it separate for backward compat.
            return LocalSLMProvider(
                base_url=provider_record.endpoint or "http://localhost:11434/v1"
            )
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
        
        # If no providers found or DB failed, check for environment-based providers
        if not providers:
            logger.info("No DB providers found, checking environment variables")
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

            if providers_list:
                # Sort by priority
                providers_list.sort(key=lambda x: x.priority)
                logger.info(
                    "Using %s environment-based providers for tier '%s': %s",
                    len(providers_list),
                    task_tier,
                    [p.name for p in providers_list],
                )
                providers = providers_list

        # Phase C local-first fallback: packaged desktop should always attempt
        # the local Ollama/vLLM adapter after cloud providers have failed.
        if self._desktop_local_first_enabled():
            local_types = {"local_slm", "ollama", "vllm"}
            has_local = any(str(getattr(provider, "provider_type", "")).lower() in local_types for provider in providers)
            if not has_local:
                class DesktopLocalProvider:
                    id = "desktop-local-slm"
                    name = "desktop-local-slm"
                    provider_type = "local_slm"
                    endpoint = os.environ.get("LOCAL_SLM_BASE_URL", "http://localhost:11434/v1")
                    deployment_name = None
                    api_version = None
                    model_id = os.environ.get("LOCAL_SLM_MODEL", default_model_for_provider("ollama"))
                    priority = 999
                    timeout_seconds = LLMGateway._positive_int(
                        os.environ.get("LOCAL_SLM_TIMEOUT_SECONDS"),
                        5,
                        minimum=1,
                        maximum=60,
                    )
                    max_retries = 1

                    def get_api_key(self):
                        return None

                providers.append(DesktopLocalProvider())
                if task_tier not in {"trivial", "moderate", "t1", "t2", "fast_chat", "structured_workflow"}:
                    meta["offline_guard"] = "desktop_local_slm_tier_cap"
                    meta["original_tier"] = task_tier
                    task_tier = "moderate"
                logger.info("Desktop local SLM fallback registered for gateway routing")
        
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

        # Routing Optimization: Prefer Local SLMs for L1/L2 (trivial/moderate) tasks
        if task_tier in ["trivial", "moderate", "t1", "t2"]:
            # Move local_slm/ollama/vllm to the front of the list
            locals = [p for p in providers if p.provider_type in ["local_slm", "ollama", "vllm"]]
            remotes = [p for p in providers if p not in locals]
            return locals + remotes

        return providers

    def _build_response(
        self,
        result: dict,
        run_id: str,
        provider: LLMProvider,
        model: str,
        latency_ms: int,
        *,
        escalation_meta: dict | None = None,
    ) -> GatewayResponse:
        usage_data = result.get("usage", {})
        usage_payload = {
            "tokens_in": usage_data.get("prompt_tokens", 0),
            "tokens_out": usage_data.get("completion_tokens", 0),
            "latency_ms": latency_ms,
        }
        if isinstance(usage_data, dict) and "estimated_cost_usd" in usage_data:
            usage_payload["estimated_cost_usd"] = usage_data.get("estimated_cost_usd")

        tier = result.get("tier")
        content = result.get("answer", "")
        _tier_exclusions = {"", "0", "t0", "1", "t1", "trivial"}
        if tier and str(tier).lower().strip() not in _tier_exclusions:
            content = content + "\n\n" + self._audit_footer(result, tier, latency_ms)

        _esc = escalation_meta or {}
        return GatewayResponse(
            content=content,
            run_id=run_id,
            provider_used=provider.provider_type,
            model_used=model,
            usage=usage_payload,
            ok=result.get("ok", True),
            coordinate=result.get("coordinate"),
            tier=tier,
            layers=result.get("layers"),
            trace=result.get("trace"),
            explainability=result.get("explainability"),
            warnings=list(result.get("warnings", [])),
            error=result.get("error"),
            escalation_tier=_esc.get("escalation_tier"),
            escalation_reason=_esc.get("escalation_reason"),
            escalation_label=_esc.get("escalation_label"),
            meta=dict(_esc),  # carries local_model_acceleration if present
        )

    @staticmethod
    def _audit_footer(result: dict, tier, latency_ms: int) -> str:
        """Return the spec Section 11.2 canonical audit footer for Tier 2+ responses."""
        expl = result.get("explainability") or {}
        raw_coord = result.get("coordinate") or {}
        coordinate = raw_coord if isinstance(raw_coord, dict) else {}
        active_axes = coordinate.get("active_axes") or []
        personas = expl.get("personas_invoked") or []
        confidence = result.get("confidence", 0.0)
        steps = result.get("refinement_steps") or []
        compliance_flags = result.get("compliance_flags") or "None"
        assumption = expl.get("key_assumption", "Not specified")
        consequence = expl.get("consequence_if_wrong", "Not specified")

        axes_str = ", ".join(str(a) for a in active_axes) if active_axes else "Not resolved"
        personas_str = ", ".join(str(p) for p in personas) if personas else "Not recorded"
        steps_str = ", ".join(str(s) for s in steps) if steps else "None"
        flags_str = str(compliance_flags) if isinstance(compliance_flags, str) else ", ".join(str(f) for f in compliance_flags)

        return (
            f"[UKG Audit Trace]\n"
            f"Tier: {tier}\n"
            f"Active Axes: {axes_str}\n"
            f"Personas Invoked: {personas_str}\n"
            f"Confidence: {confidence:.3f}\n"
            f"Refinement Steps Executed: {steps_str}\n"
            f"Compliance Flags: {flags_str}\n"
            f"Key Assumption to Verify: {assumption}\n"
            f"What Changes if Wrong: {consequence}"
        )

    def _error_response(self, run_id: str, error: str, start_time: datetime, request: GatewayRequest) -> GatewayResponse:
        latency_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
        public_error = self._public_error_message(error)
        if request.meta.get("offline_guard") == "desktop_local_slm_tier_cap":
            public_error = (
                "Local-first desktop mode could not reach a configured cloud provider or the local SLM "
                "at localhost:11434. Start Ollama/vLLM locally or configure a provider key."
            )
        return GatewayResponse(
            content="",
            run_id=run_id,
            provider_used="none",
            model_used=request.model or "unknown",
            usage={"latency_ms": latency_ms},
            ok=False,
            error=public_error,
        )
    
    
    @staticmethod
    def _recent_context_summary(
        messages: list[dict[str, Any]] | None,
        limit: int = 5,
        max_chars: int = 240,
    ) -> str:
        """Summarize the prior turns (excluding the latest message) for
        Crescendo detection by the defense supervisor."""
        prior = [m for m in (messages or [])[:-1] if isinstance(m, dict)]
        lines: list[str] = []
        for message in prior[-limit:]:
            role = str(message.get("role", "user"))
            content = message.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    part.get("text", "") for part in content if isinstance(part, dict)
                )
            text = str(content)[:max_chars].strip()
            if text:
                lines.append(f"{role}: {text}")
        return "\n".join(lines)

    def _screen_with_defense_supervisor(
        self, request: GatewayRequest, query: str
    ) -> Optional[str]:
        """Run LLM-backed security screening for pipeline queries (N2).

        Returns an error message when the request must be blocked, else
        None. The full verdict is stored in request.meta["defense_supervisor"].
        Fail-open: any wiring error allows the request (the pattern shields
        in governance.prepare_request already ran).
        """
        if not request.run_ukg_pipeline:
            return None
        try:
            from backend.security.defense_supervisor import get_defense_supervisor

            supervisor = get_defense_supervisor()
            if not supervisor.enabled():
                return None
            verdict = supervisor.screen(
                query,
                context_summary=self._recent_context_summary(request.messages),
                user_role="owner",
            )
            request.meta["defense_supervisor"] = verdict
            # HONEYPOT collapses to BLOCK by design: this is a single-user,
            # local-first app (one OS owner), so there is no external adversary
            # to feed a decoy response — blocking is the correct, conservative
            # action for both verdicts. The distinct HONEYPOT label is preserved
            # in request.meta for the audit trail. (A3-4; user_role is "owner".)
            if verdict.get("available") and verdict.get("recommended_action") in {
                "BLOCK",
                "HONEYPOT",
            }:
                return verdict.get("reason") or "Blocked by security supervisor"
        except Exception as exc:  # noqa: BLE001
            logger.warning("Defense supervisor wiring failed open: %s", exc)
        return None

    def _extract_query(self, messages: list[dict[str, Any]]) -> str:
        """Extract user query from messages, handling multimodal content."""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, list):
                    # Extract text parts from multimodal content
                    text_parts = [part.get("text", "") for part in content if part.get("type") == "text"]
                    return " ".join(text_parts)
                return content
        return ""

    def _replace_latest_user_message(self, messages: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
        """Override the latest user message content (used after prompt-template rendering)."""
        cloned_messages = [dict(message) for message in messages]
        for index in range(len(cloned_messages) - 1, -1, -1):
            if cloned_messages[index].get("role") == "user":
                cloned_messages[index]["content"] = query
                return cloned_messages

        cloned_messages.append({"role": "user", "content": query})
        return cloned_messages
    
    async def _run_quad_analysis(
        self,
        query: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Run query through QuadPersonaEngine and PodOrchestrator."""
        try:
            from backend.quad_persona.quad_engine import create_quad_persona_engine
            from backend.truth_engine.truth_core.persona_scaling_bridge import (
                orchestration_summary,
                scaling_decision_from_sufficiency,
            )
            from core.persona.quad.persona_scaling.sufficiency import GatewayPersonaSufficiencyTool as PersonaSufficiencyTool
            from core.persona.quad.pod_orchestrator import create_pod_orchestrator
            engine = create_quad_persona_engine(llm_gateway=self)
            
            # Run the concurrent analysis
            analysis = await engine.run_quad_analysis(query, context)
            perspectives = analysis.get("perspectives", {})
            active_axes = context.get("active_axes") or context.get("mapped_axes") or [8, 9, 10, 11]
            sufficiency = PersonaSufficiencyTool().evaluate(
                query,
                active_axes,
                perspectives,
                {"domain": context.get("risk_domain", context.get("domain", "standard")), "tags": context.get("tags", [])},
            )
            if context.get("force_expanded_committee"):
                sufficiency["mode"] = "expanded_committee"
                sufficiency["spawn"] = sufficiency.get("spawn") or {
                    "knowledge": 1,
                    "sector": 1,
                    "regulatory": 1,
                    "compliance": 1,
                }

            scaling_decision = scaling_decision_from_sufficiency(sufficiency)
            orchestration_state = create_pod_orchestrator().orchestrate(
                query,
                {**context, "query_id": context.get("query_id") or str(uuid.uuid4())},
                scaling_decision,
                base_persona_results=perspectives,
            )
            pod_summary = orchestration_summary(orchestration_state)
            self.__class__._last_quad_analysis_status = pod_summary
            analysis_synthesis = analysis.get("synthesis", "Failed to synthesize persona perspectives.")
            if isinstance(analysis_synthesis, dict):
                analysis_synthesis = analysis_synthesis.get("summary", "Failed to synthesize persona perspectives.")
            answer = orchestration_state.final_synthesis or analysis_synthesis
            
            return {
                "ok": True,
                "answer": answer,
                "trace": [
                    {"ka_id": "PersonaAnalysis", "status": "pass", "output": perspectives},
                    {"ka_id": "PodOrchestrator", "status": "pass", "output": pod_summary},
                    {"ka_id": "Synthesis", "status": "pass", "output": {"summary": answer[:200] + "..."}}
                ],
                "confidence_score": pod_summary["collective_confidence"] or analysis.get("metadata", {}).get("confidence", 0.9),
                "tier": "high_stakes",
                "coordinate": "AXIS_07_COMPLIANCE", # Default coordinate for persona analysis
                "metadata": {"quad_analysis_status": pod_summary},
            }
        except Exception as e:
            logger.error(f"Quad persona analysis failed: {e}")
            self.__class__._last_quad_analysis_status = {
                "pod_count": 0,
                "collective_confidence": 0.0,
                "mode": "error",
                "status": "failed",
            }
            return {"ok": False, "error": str(e)}

    async def _run_ukg_overlay(
        self,
        sdk_provider: Any,
        model: str,
        query: str,
        run_id: str,
        user_id: str,
        session_id: Optional[str],
        meta: dict[str, Any],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Run query through UKGOverlay."""
        try:
            from ukg_sdk.overlay import UKGOverlay
        except ImportError as e:
            logger.warning(f"UKGOverlay not available: {e}")
            return await self._direct_llm_call_fallback(
                sdk_provider, model, query, temperature, max_tokens
            )
        
        if sdk_provider is None:
            return {"ok": False, "error": "No provider configured"}
        
        # Create overlay instance
        overlay = UKGOverlay(
            provider=sdk_provider,
            model=model,
            data_dir=SDK_PATH / "ukg_sdk" / "data",
        )
        
        # Get correlation ID from request context
        from flask import g
        correlation_id = getattr(g, 'correlation_id', None)
        
        # Run through UKG pipeline
        result = await overlay.run(
            query=query,
            user_id=user_id,
            session_id=session_id,
            correlation_id=correlation_id,
            meta=meta,
            temperature=temperature,
            max_tokens=max_tokens,
            tier_override=meta.get("dmrf_tier"),
        )
        
        # Connect SDK trace to TraceRun/TraceStage models
        await self._create_trace_run(result, query, run_id, user_id, session_id, model)
        
        return result
    
    async def _create_trace_run(
        self,
        sdk_result: dict[str, Any],
        query: str,
        run_id: str,
        user_id: str,
        session_id: Optional[str],
        model: str,
    ) -> None:
        """Create TraceRun and TraceStage records from SDK result."""
        try:
            from models import TraceRun, TraceStage
            try:
                from extensions import db
            except ImportError:
                # Final fallback
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                from extensions import db
            import uuid
            
            # Create TraceRun
            from flask import g
            correlation_id = getattr(g, 'correlation_id', None)
            model_version = (
                sdk_result.get("model_version")
                or (sdk_result.get("metadata", {}) or {}).get("model_version")
                or "unknown"
            )
            
            sdk_tier = str(sdk_result.get("tier") or "")
            trace_run_id = uuid.UUID(run_id)
            run = TraceRun(
                run_id=trace_run_id,
                session_id=uuid.UUID(session_id) if session_id else None,
                user_id=int(user_id) if user_id else None,
                status="pass" if sdk_result.get("ok") else "fail",
                model_name=model,
                model_version=model_version,
                input_message=query,
                final_answer=sdk_result.get("answer", ""),
                correlation_id=correlation_id,
                confidence=sdk_result.get("confidence", 0.85),
                tier=sdk_tier if sdk_tier else None,
                layers_executed=sdk_result.get("layers"),
                truthgate_decision=sdk_result.get("truthgate_decision"),
            )
            db.session.add(run)
            db.session.flush()  # populate run.run_id before child TraceStage rows reference it

            # Create TraceStages from SDK trace
            trace = sdk_result.get("trace", [])
            emitted_stages: list[Any] = []
            for i, trace_item in enumerate(trace):
                stage = TraceStage(
                    run_id=run.run_id,
                    name=trace_item.get("ka_id", f"Stage-{i}"),
                    stage_type="layer",
                    layer_index=i + 1,
                    status=trace_item.get("status", "pass"),
                    outputs=trace_item.get("output", {}),
                )
                db.session.add(stage)
                emitted_stages.append(stage)

            db.session.commit()
            logger.info(f"Created TraceRun {run.run_id} with {len(trace)} stages")
            for stage in emitted_stages:
                try:
                    from backend.websocket import emit_trace_stage_update
                    emit_trace_stage_update(run.run_id, stage.to_dict())
                except Exception as emit_exc:
                    logger.debug("Trace stage websocket emit skipped: %s", emit_exc)

            # Compute F-CONF-01 canonical confidence and update the run
            try:
                from backend.truth_engine.confidence_calculator import ConfidenceCalculator
                canonical_conf = ConfidenceCalculator().calculate(
                    run,
                    ka_results=sdk_result.get("trace"),
                    gate_decision=sdk_result.get("truthgate_decision"),
                )
                run.confidence = canonical_conf
                db.session.add(run)
                db.session.commit()
            except Exception as conf_exc:
                logger.warning("F-CONF-01 calculation failed (non-fatal): %s", conf_exc)

            # Commit audit bundle for Tier 2+ runs
            _tier_exclusions = {"", "0", "t0", "1", "t1", "trivial"}
            if sdk_tier and str(sdk_tier).lower().strip() not in _tier_exclusions:
                try:
                    from backend.truth_engine.truth_memory.commit_service import TruthMemoryCommitService
                    TruthMemoryCommitService().commit(run, db.session)
                except Exception as commit_exc:
                    logger.warning("Audit bundle commit failed (non-fatal): %s", commit_exc)
            
        except Exception as e:
            logger.warning(f"Failed to create trace records: {e}")
            # Don't fail the request if tracing fails

    
    async def _direct_llm_call(
        self,
        sdk_provider: Any,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Direct LLM call without UKG pipeline."""
        if sdk_provider is None:
            return {"ok": False, "error": "No provider configured"}
        
        try:
            response = await sdk_provider.complete(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            # LocalSLMProvider signals errors via response.raw["ok"] == False rather
            # than raising — cloud SDK providers raise exceptions instead. Check the
            # sentinel so local model failures propagate correctly.
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
    
    async def _direct_llm_call_fallback(
        self,
        sdk_provider: Any,
        model: str,
        query: str,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Fallback direct call when SDK not available."""
        messages = [{"role": "user", "content": query}]
        return await self._direct_llm_call(sdk_provider, model, messages, temperature, max_tokens)
    
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

    async def _get_recent_history(self, session_id: str, limit: int = 10) -> list[dict]:
        """Load recent messages for context."""
        try:
            import uuid
            messages = ChatMessage.query.filter_by(session_id=uuid.UUID(session_id))\
                .order_by(ChatMessage.created_at.desc())\
                .limit(limit).all()
            return [{"role": m.role, "content": m.content} for m in reversed(messages)]
        except Exception as e:
            logger.warning(f"Failed to load chat history: {e}")
            return []

# Singleton instance
_gateway_instance = None

def get_gateway() -> LLMGateway:
    """Get or create global LLMGateway instance."""
    global _gateway_instance
    if _gateway_instance is None:
        try:
            from extensions import db
            _gateway_instance = LLMGateway(db_session=db.session)
        except (ImportError, RuntimeError):
            # Fallback for tests/environments without db
            _gateway_instance = LLMGateway()
    return _gateway_instance

