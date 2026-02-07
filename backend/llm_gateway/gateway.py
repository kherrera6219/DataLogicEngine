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

from models import LLMProvider, LLMProviderUsage, ChatSession, ChatMessage

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
        
        # 2. Extract Query and Load History
        query = self._extract_query(request.messages)
        user_id_str = str(request.user_id) if request.user_id else "anonymous"
        
        history = []
        if request.session_id:
            # Save user message once before trying providers
            await self._save_chat_message(request.session_id, request.user_id, "user", query)
            # Load history for context injection
            history = await self._get_recent_history(request.session_id)
        
        # 3. Try providers in order
        for provider_record in providers:
            cb = self._get_circuit_breaker(str(provider_record.id))
            
            if not cb.can_execute():
                logger.warning(f"Circuit OPEN for provider {provider_record.name}, skipping...")
                continue
            
            # Implementation of Retries with Exponential Backoff + Jitter
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # 4. Create SDK provider and run
                    sdk_provider = self._create_sdk_provider(provider_record)
                    model = request.model or (provider_record.model_id if provider_record else "gpt-4")
                    
                    full_messages = history + request.messages
                    
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
                        
                        # Inject RAG context into meta for UKG overlay
                        augmented_meta = {**request.meta, "rag_context": rag_context, "chat_history": history}
                        
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
                                user_id=user_id_str,
                                session_id=request.session_id,
                                meta=augmented_meta,
                                temperature=request.temperature,
                                max_tokens=request.max_tokens or 1024,
                            )
                    else:
                        result = await self._direct_llm_call(
                            sdk_provider=sdk_provider,
                            model=model,
                            messages=full_messages,
                            temperature=request.temperature,
                            max_tokens=request.max_tokens or 1024,
                        )
                    
                    if result.get("ok", True):
                        cb.record_success()
                        latency_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
                        await self._record_usage(provider_record.id, request.user_id, request.api_key_id, run_id, model, 
                                              result.get("usage", {}).get("prompt_tokens", 0), 
                                              result.get("usage", {}).get("completion_tokens", 0), 
                                              latency_ms, True)
                        
                        if request.session_id:
                            await self._save_chat_message(request.session_id, request.user_id, "assistant", result.get("answer", ""), run_id)
                                              
                        return self._build_response(result, run_id, provider_record, model, latency_ms)
                    
                    # If provider returned !ok but might be retryable (e.g., 429, 503)
                    last_error = result.get("error", "Unknown provider error")
                    logger.warning(f"Provider {provider_record.name} attempt {attempt+1} failed: {last_error}")
                    
                    if attempt < max_retries - 1:
                        import random
                        sleep_time = (2 ** attempt) + random.uniform(0, 1)
                        await asyncio.sleep(sleep_time)
                    else:
                        cb.record_failure()
                        
                except Exception as e:
                    last_error = str(e)
                    logger.error(f"Provider {provider_record.name} attempt {attempt+1} exception: {e}")
                    if attempt < max_retries - 1:
                        import random
                        sleep_time = (2 ** attempt) + random.uniform(0, 1)
                        await asyncio.sleep(sleep_time)
                    else:
                        cb.record_failure()
                        break # Try next provider

        # All eligible providers failed or were unavailable.
        return self._error_response(
            run_id,
            last_error or "All providers failed",
            start_time,
            request,
        )

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
             return GoogleGeminiProvider(api_key=api_key, model=provider_record.model_id or "gemini-2.5-pro")
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
            
            # Logic (2026 Generation) - 3 Layer Redundancy
            # We need 3 slots: [Primary, Failover 1 (Cross-Provider), Failover 2 (Safety/Speed)]
            
            openai_key = os.environ.get("OPENAI_API_KEY")
            google_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
            anthropic_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("anthropic_API_KEY")
            openai_primary_model = os.environ.get("OPENAI_MODEL_PRIMARY", "gpt-5.2-pro")
            openai_standard_model = os.environ.get("OPENAI_MODEL_STANDARD", "gpt-5.2")
            openai_fast_model = os.environ.get("OPENAI_MODEL_FAST", "gpt-5-mini")
            openai_nano_model = os.environ.get("OPENAI_MODEL_NANO", "gpt-5-nano")
            openai_long_context_model = os.environ.get("OPENAI_MODEL_LONG_CONTEXT", "gpt-4.1")
            openai_research_model = os.environ.get("OPENAI_MODEL_RESEARCH", "o3-deep-research")
            google_primary_model = os.environ.get("GOOGLE_MODEL_PRIMARY", "gemini-2.5-pro")
            google_fast_model = os.environ.get("GOOGLE_MODEL_FAST", "gemini-2.5-flash")
            anthropic_primary_model = os.environ.get("ANTHROPIC_MODEL_PRIMARY", "claude-opus-4-6")

            providers_list = []

            # Helpers to add unique providers
            def add_provider(p_list, name, p_type, model, prio):
                # Simple check to avoid exact duplicates if logic overlaps
                for p in p_list:
                    if p.name == name: return
                p_list.append(EnvProvider(name, p_type, priority=prio, model=model))

            # --- Construct 3-Layer List based on Tier ---
            
            if task_tier == "complex_reasoning":
                # Layer 1: Peak Intelligence (OpenAI)
                if openai_key: add_provider(providers_list, "openai-primary", "openai", openai_primary_model, 1)
                # Layer 2: Cross-Provider Strong (Google)
                if google_key: add_provider(providers_list, "google-fallback", "google", google_primary_model, 2)
                # Layer 3: Same-Provider Standard (OpenAI) or Other
                if openai_key: add_provider(providers_list, "openai-safety", "openai", openai_standard_model, 3)
                elif google_key: add_provider(providers_list, "google-safety", "google", google_fast_model, 3)

            elif task_tier == "security_defense":
                # High-Stakes Security Analysis routing
                # Layer 1: Best Reasoning Available (OpenAI)
                if openai_key: add_provider(providers_list, "openai-defense", "openai", openai_primary_model, 1)
                # Layer 2: Strongest Alternate (Google)
                if google_key: add_provider(providers_list, "google-defense", "google", google_primary_model, 2)
                # Layer 3: Fallback (OpenAI Standard)
                if openai_key: add_provider(providers_list, "openai-defense-fallback", "openai", openai_standard_model, 3)

            elif task_tier == "deep_research":
                # Layer 1: Autonomous Research (OpenAI)
                if openai_key: add_provider(providers_list, "openai-research", "openai", openai_research_model, 1)
                # Layer 2: Strong Reasoning (Google)
                if google_key: add_provider(providers_list, "google-fallback", "google", google_primary_model, 2)
                # Layer 3: High Logic (OpenAI)
                if openai_key: add_provider(providers_list, "openai-fallback", "openai", openai_primary_model, 3)

            elif task_tier in ["rag_heavy", "context_heavy"]:
                # Layer 1: Massive Context (Google)
                if google_key: add_provider(providers_list, "google-context", "google", google_primary_model, 1)
                # Layer 2: Large Context Reliability (OpenAI)
                if openai_key: add_provider(providers_list, "openai-fallback", "openai", openai_long_context_model, 2)
                # Layer 3: Speed/Capacity (Google)
                if google_key: add_provider(providers_list, "google-flash", "google", google_fast_model, 3)

            elif task_tier in ["fast_chat", "structured_workflow"]:
                # Layer 1: Speed King (Google)
                if google_key: add_provider(providers_list, "google-flash", "google", google_fast_model, 1)
                # Layer 2: Structured Efficient (OpenAI)
                if openai_key: add_provider(providers_list, "openai-mini", "openai", openai_fast_model, 2)
                # Layer 3: Robust Fallback (Google)
                if google_key: add_provider(providers_list, "google-std", "google", google_primary_model, 3)
                elif openai_key: add_provider(providers_list, "openai-nano", "openai", openai_nano_model, 3)

            else:
                # Default / General Chat
                # Layer 1: Balanced (OpenAI)
                if openai_key: add_provider(providers_list, "openai-default", "openai", openai_standard_model, 1)
                # Layer 2: Balanced (Google)
                if google_key: add_provider(providers_list, "google-default", "google", google_primary_model, 2)
                # Layer 3: Speed (Google)
                if google_key: add_provider(providers_list, "google-speed", "google", google_fast_model, 3)
            
            # If we still have space and Anthropic key exists, inject it as ultimate backup
            if anthropic_key and len(providers_list) < 3:
                add_provider(providers_list, "anthropic-backup", "anthropic", anthropic_primary_model, 4)

            if providers_list:
                # Sort by priority
                providers_list.sort(key=lambda x: x.priority)
                logger.info(f"Using {len(providers_list)} environment-based providers for tier '{task_tier}': {[p.name for p in providers_list]}")
                return providers_list
        
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
            from models import TraceRun, TraceStage
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
                if not user_id: return
                
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

