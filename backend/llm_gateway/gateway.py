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
import logging
import os
import sys
import uuid
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, AsyncIterator, Optional
from dataclasses import dataclass, field

# Add SDK to path
SDK_PATH = Path(__file__).resolve().parent.parent.parent / "sdk" / "UKG_Python_SDK"
if str(SDK_PATH) not in sys.path:
    sys.path.insert(0, str(SDK_PATH))

from backend.llm_gateway.models import LLMProvider, LLMProviderUsage

logger = logging.getLogger(__name__)


@dataclass
class GatewayRequest:
    """Incoming gateway request."""
    messages: list[dict[str, str]]
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
    usage: dict[str, int]
    ok: bool = True
    # UKG enhancements
    coordinate: Optional[str] = None
    tier: Optional[str] = None
    layers: Optional[list[str]] = None
    trace: Optional[list[dict]] = None
    explainability: Optional[dict] = None
    warnings: list[str] = field(default_factory=list)
    error: Optional[str] = None


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


class LLMGateway:
    """
    Main gateway class that routes requests through UKG SDK.
    """
    
    # Class-level circuit breaker state
    _circuit_breakers: dict[str, CircuitBreaker] = {}
    
    def __init__(self, db_session=None):
        self.db = db_session
        self._overlays: dict[str, Any] = {}
    
    def _get_circuit_breaker(self, provider_id: str) -> CircuitBreaker:
        if provider_id not in self._circuit_breakers:
            self._circuit_breakers[provider_id] = CircuitBreaker(provider_id)
        return self._circuit_breakers[provider_id]
    
    async def process(self, request: GatewayRequest) -> GatewayResponse:
        """
        Process a gateway request with failover and circuit breaker.
        """
        run_id = str(uuid.uuid4())
        start_time = datetime.now(UTC)
        
        # 1. Get eligible providers
        providers = await self._get_eligible_providers(request.provider)
        if not providers:
            return self._error_response(run_id, "No active providers found", start_time, request)

        last_error = None
        
        # 2. Try providers in order
        for provider_record in providers:
            cb = self._get_circuit_breaker(str(provider_record.id))
            
            if not cb.can_execute():
                logger.warning(f"Circuit OPEN for provider {provider_record.name}, skipping...")
                continue
                
            try:
                # 3. Create SDK provider and run
                sdk_provider = self._create_sdk_provider(provider_record)
                model = request.model or (provider_record.model_id if provider_record else "gpt-4")
                query = self._extract_query(request.messages)
                user_id = str(request.user_id) if request.user_id else "anonymous"
                
                if request.run_ukg_pipeline:
                    result = await self._run_ukg_overlay(
                        sdk_provider=sdk_provider,
                        model=model,
                        query=query,
                        user_id=user_id,
                        session_id=request.session_id,
                        meta=request.meta,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens or 1024,
                    )
                else:
                    result = await self._direct_llm_call(
                        sdk_provider=sdk_provider,
                        model=model,
                        messages=request.messages,
                        temperature=request.temperature,
                        max_tokens=request.max_tokens or 1024,
                    )
                
                if result.get("ok", True):
                    cb.record_success()
                    
                    # Record usage and return
                    latency_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
                    await self._record_usage(provider_record.id, request.user_id, request.api_key_id, run_id, model, 
                                          result.get("usage", {}).get("prompt_tokens", 0), 
                                          result.get("usage", {}).get("completion_tokens", 0), 
                                          latency_ms, True)
                                          
                    return self._build_response(result, run_id, provider_record, model, latency_ms)
                else:
                    last_error = result.get("error", "Unknown provider error")
                    cb.record_failure()
                    logger.warning(f"Provider {provider_record.name} failed: {last_error}")
                    
            except Exception as e:
                cb.record_failure()
                last_error = str(e)
                logger.error(f"Provider {provider_record.name} exception: {e}")
                continue
                
        # If all providers failed
        error_msg = f"All providers failed. Last error: {last_error}"
        return self._error_response(run_id, error_msg, start_time, request)

    async def _get_eligible_providers(self, provider_name: Optional[str]) -> list[LLMProvider]:
        """Get list of active providers ordered by priority."""
        if provider_name:
            query = LLMProvider.query.filter(
                (LLMProvider.name == provider_name) | (LLMProvider.provider_type == provider_name),
                LLMProvider.is_active == True
            )
        else:
            query = LLMProvider.query.filter_by(is_active=True)
            
        return query.order_by(LLMProvider.priority).all()

    def _build_response(self, result: dict, run_id: str, provider: LLMProvider, model: str, latency_ms: int) -> GatewayResponse:
        usage_data = result.get("usage", {})
        return GatewayResponse(
            content=result.get("answer", ""),
            run_id=run_id,
            provider_used=provider.provider_type,
            model_used=model,
            usage={
                "tokens_in": usage_data.get("prompt_tokens", 0),
                "tokens_out": usage_data.get("completion_tokens", 0),
                "latency_ms": latency_ms,
            },
            ok=result.get("ok", True),
            coordinate=result.get("coordinate"),
            tier=result.get("tier"),
            layers=result.get("layers"),
            trace=result.get("trace"),
            explainability=result.get("explainability"),
            error=result.get("error"),
        )

    def _error_response(self, run_id: str, error: str, start_time: datetime, request: GatewayRequest) -> GatewayResponse:
        latency_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
        return GatewayResponse(
            content="",
            run_id=run_id,
            provider_used="none",
            model_used=request.model or "unknown",
            usage={"latency_ms": latency_ms},
            ok=False,
            error=error
        )
    
    async def _get_provider_record(self, provider_name: Optional[str]) -> Optional[LLMProvider]:
        """Get provider config from database."""
        if provider_name:
            record = LLMProvider.query.filter_by(name=provider_name, is_active=True).first()
            if not record:
                record = LLMProvider.query.filter_by(provider_type=provider_name, is_active=True).first()
            return record
        
        # Get default
        record = LLMProvider.query.filter_by(is_default=True, is_active=True).first()
        if not record:
            record = LLMProvider.query.filter_by(is_active=True).order_by(LLMProvider.priority).first()
        return record
    
    def _create_sdk_provider(self, provider_record: Optional[LLMProvider]) -> Any:
        """Create SDK provider instance from database config."""
        try:
            from ukg_sdk.providers import OpenAIProvider, AzureOpenAIProvider, AnthropicProvider
        except ImportError:
            logger.warning("UKG SDK providers not available, using fallback")
            return None
        
        if not provider_record:
            # Fallback to environment
            return OpenAIProvider()
        
        api_key = provider_record.get_api_key()
        provider_type = provider_record.provider_type.lower()
        
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
        else:
            # Default to OpenAI-compatible
            return OpenAIProvider(api_key=api_key, base_url=provider_record.endpoint)
    
    def _extract_query(self, messages: list[dict[str, str]]) -> str:
        """Extract user query from messages."""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                return msg.get("content", "")
        return messages[-1].get("content", "") if messages else ""
    
    async def _run_ukg_overlay(
        self,
        sdk_provider: Any,
        model: str,
        query: str,
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
        )
        
        # Connect SDK trace to TraceRun/TraceStage models
        await self._create_trace_run(result, query, user_id, session_id, model)
        
        return result
    
    async def _create_trace_run(
        self,
        sdk_result: dict[str, Any],
        query: str,
        user_id: str,
        session_id: Optional[str],
        model: str,
    ) -> None:
        """Create TraceRun and TraceStage records from SDK result."""
        try:
            from backend.tracing.models import TraceRun, TraceStage
            from backend.extensions import db
            import uuid
            
            # Create TraceRun
            from flask import g
            correlation_id = getattr(g, 'correlation_id', None)
            
            run = TraceRun(
                session_id=uuid.UUID(session_id) if session_id else None,
                status="pass" if sdk_result.get("ok") else "fail",
                model_name=model,
                input_message=query,
                final_answer=sdk_result.get("answer", ""),
                correlation_id=correlation_id,
                confidence=0.85,  # From SDK result if available
            )
            db.session.add(run)
            
            # Create TraceStages from SDK trace
            trace = sdk_result.get("trace", [])
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
            
            db.session.commit()
            logger.info(f"Created TraceRun {run.run_id} with {len(trace)} stages")
            
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
            return {
                "ok": True,
                "answer": response.text,
                "usage": response.usage,
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
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Record usage for analytics."""
        try:
            from backend.extensions import db
            
            usage = LLMProviderUsage(
                provider_id=provider_id,
                user_id=user_id,
                api_key_id=uuid.UUID(api_key_id) if api_key_id else None,
                run_id=uuid.UUID(run_id),
                model=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                latency_ms=latency_ms,
                success=success,
                error_code=error_code,
                error_message=error_message,
            )
            db.session.add(usage)
            db.session.commit()
            
            if provider_id:
                provider = LLMProvider.query.get(provider_id)
                if provider:
                    provider.last_used_at = datetime.now(UTC)
                    db.session.commit()
                    
        except Exception as e:
            logger.error(f"Failed to record usage: {e}")
    
    async def close(self) -> None:
        """Clean up."""
        self._overlays.clear()
