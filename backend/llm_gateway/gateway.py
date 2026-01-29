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
        providers = await self._get_eligible_providers(request.provider, request.meta)
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
                    # Retrieve relevant context from RAG (VectorStore)
                    rag_context = ""
                    if request.meta.get("use_rag", True):
                        try:
                            from backend.services.rag_service import get_rag_service
                            rag = get_rag_service()
                            rag_context = rag.get_context_for_query(query, max_tokens=1500)
                            if rag_context:
                                logger.debug(f"Retrieved RAG context: {len(rag_context)} chars")
                        except Exception as e:
                            logger.warning(f"RAG context retrieval failed: {e}")
                    
                    # Inject RAG context into meta for UKG overlay
                    augmented_meta = {**request.meta, "rag_context": rag_context}
                    
                    # Decide between standard overlay and quad persona analysis
                    if request.mode == "quad" or request.meta.get("quad_persona", False):
                        result = await self._run_quad_analysis(
                            query=query,
                            context=augmented_meta,
                        )
                    else:
                        result = await self._run_ukg_overlay(
                            sdk_provider=sdk_provider,
                            model=model,
                            query=query,
                            user_id=user_id,
                            session_id=request.session_id,
                            meta=augmented_meta,
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

    def _create_sdk_provider(self, provider_record: Optional[LLMProvider]) -> Any:
        """Create SDK provider instance from database config."""
        import os
        try:
            from ukg_sdk.providers import (
                OpenAIProvider, 
                AzureOpenAIProvider, 
                AnthropicProvider, 
                LocalSLMProvider,
                GoogleGeminiProvider
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
        
        provider_type = provider_record.provider_type.lower()
        
        # Fallback to environment variable if decryption failed
        if not api_key:
            env_key_map = {
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "azure": "AZURE_OPENAI_API_KEY",
                "google": "GOOGLE_API_KEY",
                "gemini": "GMENI_API_KEY"
            }
            env_var = env_key_map.get(provider_type, f"{provider_type.upper()}_API_KEY")
            api_key = os.environ.get(env_var)
            
            # Special check for Gemini if Google key missing
            if provider_type == "google" and not api_key:
                api_key = os.environ.get("GEMINI_API_KEY")

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
             return GoogleGeminiProvider(api_key=api_key, model=provider_record.model_id or "gemini-pro")
        elif provider_type in ["local_slm", "ollama", "vllm"]:
            return LocalSLMProvider(base_url=provider_record.endpoint or "http://localhost:11434/v1")
        else:
            # Default to OpenAI-compatible
            return OpenAIProvider(api_key=api_key, base_url=provider_record.endpoint)

    async def _get_eligible_providers(self, preferred_name: Optional[str] = None, meta: dict = None) -> list[LLMProvider]:
        """Get list of active providers ordered by priority and task complexity."""
        import os
        meta = meta or {}
        task_tier = meta.get("tier", "high_stakes").lower()
        use_rag = meta.get("use_rag", False)
        
        providers = []
        
        # Try to get providers from database
        try:
            if preferred_name:
                query = LLMProvider.query.filter(
                    (LLMProvider.name == preferred_name) | (LLMProvider.provider_type == preferred_name),
                    LLMProvider.is_active == True
                )
                providers = query.all()
            else:
                providers = LLMProvider.query.filter_by(is_active=True).order_by(LLMProvider.priority).all()
        except Exception as e:
            logger.warning(f"Failed to query providers from DB: {e}")
            providers = []
        
        # If no providers found or DB failed, check for environment-based providers
        if not providers:
            logger.info("No DB providers found, checking environment variables")
            # Create synthetic provider entries based on available API keys
            env_providers = []
            
            # Helper class for synthetic providers
            class EnvProvider:
                def __init__(self, name, provider_type, priority=10, model="gpt-4o"):
                    self.id = name
                    self.name = name
                    self.provider_type = provider_type
                    self.endpoint = None
                    self.deployment_name = None
                    self.api_version = None
                    self.model_id = model
                    self.priority = priority
                def get_api_key(self):
                    return None # _create_sdk_provider will fetch from env
            
            # Logic: 
            # Complex Reasoning = OpenAI o1 / GPT-5 (Priority 1)
            # RAG/Long Context = Gemini 3 Pro (Priority 1)
            # Fast Chat = Gemini 3 Flash (Priority 1)
            # Default = GPT-5 (Priority 1), Gemini 3 Pro (Priority 2)
            
            openai_key = os.environ.get("OPENAI_API_KEY")
            google_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
            
            # 1. Complex Reasoning Provider (OpenAI)
            if openai_key:
                prio = 1
                model = "gpt-5" # Default high-end
                
                if task_tier == "complex_reasoning":
                    model = "o1" # Strawberry for deep reasoning
                    prio = 1
                elif task_tier in ["rag_heavy", "fast_chat"] and google_key:
                    prio = 2 # Demote if better suited for Gemini
                
                env_providers.append(EnvProvider("openai-env", "openai", priority=prio, model=model))
            
            # 2. Context/Speed Provider (Google)
            if google_key:
                prio = 2
                model = "gemini-3-pro-preview" # Default high-end
                
                if task_tier == "rag_heavy":
                    prio = 1
                    model = "gemini-3-pro-preview" # Massive context
                elif task_tier == "fast_chat":
                    prio = 1
                    model = "gemini-3-flash-preview" # Low latency
                elif task_tier == "complex_reasoning" and openai_key:
                    prio = 2 # Demote if reasoning needed
                
                env_providers.append(EnvProvider("google-env", "google", priority=prio, model=model))
            
            if os.environ.get("ANTHROPIC_API_KEY"):
                env_providers.append(EnvProvider("anthropic-env", "anthropic", priority=3))
            
            if env_providers:
                # Sort by priority
                env_providers.sort(key=lambda x: x.priority)
                logger.info(f"Using {len(env_providers)} environment-based providers. Top: {env_providers[0].name} ({env_providers[0].model_id}) for tier {task_tier}")
                return env_providers
        
        # Routing Optimization: Prefer Local SLMs for L1/L2 (trivial/moderate) tasks
        if task_tier in ["trivial", "moderate", "t1", "t2"]:
            # Move local_slm/ollama/vllm to the front of the list
            locals = [p for p in providers if p.provider_type in ["local_slm", "ollama", "vllm"]]
            remotes = [p for p in providers if p not in locals]
            return locals + remotes
            
        return providers

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
        import os
        try:
            from ukg_sdk.providers import OpenAIProvider, AzureOpenAIProvider, AnthropicProvider, LocalSLMProvider
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
        
        # Fallback to environment variable if decryption failed
        if not api_key:
            provider_type = provider_record.provider_type.lower()
            env_key_map = {
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "azure": "AZURE_OPENAI_API_KEY",
            }
            env_var = env_key_map.get(provider_type, f"{provider_type.upper()}_API_KEY")
            api_key = os.environ.get(env_var)
            if api_key:
                logger.info(f"Using {env_var} environment variable for {provider_record.name}")
            else:
                logger.warning(f"No API key available for {provider_record.name}")
        
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
        elif provider_type in ["local_slm", "ollama", "vllm"]:
            return LocalSLMProvider(base_url=provider_record.endpoint or "http://localhost:11434/v1")
        else:
            # Default to OpenAI-compatible
            return OpenAIProvider(api_key=api_key, base_url=provider_record.endpoint)
    
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
    
    async def _run_quad_analysis(
        self,
        query: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Run query through QuadPersonaEngine for 4-way expert analysis."""
        try:
            from backend.quad_persona.quad_engine import create_quad_engine
            engine = create_quad_engine()
            
            # Run the concurrent analysis
            analysis = await engine.run_quad_analysis(query, context)
            
            return {
                "ok": True,
                "answer": analysis.get("synthesis", "Failed to synthesize persona perspectives."),
                "trace": [
                    {"ka_id": "PersonaAnalysis", "status": "pass", "output": analysis.get("perspectives", {})},
                    {"ka_id": "Synthesis", "status": "pass", "output": {"summary": analysis.get("synthesis")[:200] + "..."}}
                ],
                "confidence_score": analysis.get("metadata", {}).get("confidence", 0.9),
                "tier": "high_stakes",
                "coordinate": "AXIS_07_COMPLIANCE" # Default coordinate for persona analysis
            }
        except Exception as e:
            logger.error(f"Quad persona analysis failed: {e}")
            return {"ok": False, "error": str(e)}

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
            try:
                from extensions import db, cache
            except ImportError:
                # Final fallback
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                from extensions import db, cache
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
            try:
                from extensions import db
            except ImportError:
                import os
                import sys
                sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                from extensions import db
            
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
