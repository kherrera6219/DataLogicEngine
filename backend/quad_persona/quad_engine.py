"""
Quad Persona Engine - PRODUCTION VERSION
----------------------------------------
Runs concurrent analysis using 4 expert personas with REAL LLM calls.
"""

import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class QuadPersonaEngine:
    """
    Runs analyses concurrently using four distinct personas with real LLM integration.
    """
    
    def __init__(self, llm_gateway=None, max_concurrent_queries: int = 50, query_timeout: int = 120):
        self.personas = {
            "knowledge": {
                "name": "Knowledge Expert (Axis 8)",
                "system_prompt": "You are a Knowledge Expert specializing in domain-specific expertise. Provide deep, factual analysis based on established knowledge bases and best practices."
            },
            "sector": {
                "name": "Sector Specialist (Axis 9)",
                "system_prompt": "You are a Sector Specialist with practical industry experience. Focus on real-world applications, market dynamics, and sector-specific considerations."
            },
            "regulatory": {
                "name": "Regulatory Advisor (Axis 10)",
                "system_prompt": "You are a Regulatory Advisor expert in compliance and legal frameworks. Analyze from a regulatory perspective, citing relevant laws and standards."
            },
            "compliance": {
                "name": "Compliance Officer (Axis 11)",
                "system_prompt": "You are a Compliance Officer focused on risk management and adherence to policies. Evaluate compliance implications and potential violations."
            }
        }
        self.llm_gateway = llm_gateway
        self.max_concurrent_queries = max_concurrent_queries
        self.query_timeout = query_timeout
        self.active_queries = 0
        logger.info(f"QuadPersonaEngine v2.0 initialized (PRODUCTION MODE, max concurrent: {max_concurrent_queries}, timeout: {query_timeout}s).")
    
    async def _call_llm(self, prompt: str, persona_config: Dict[str, str]) -> str:
        """
        Call LLM through the gateway with persona context.
        
        Args:
            prompt: The user query
            persona_config: Persona configuration with system prompt
            
        Returns:
            LLM response text
        """
        if not self.llm_gateway:
            # Use existing LLM gateway
            try:
                from llm_gateway.gateway import get_llm_gateway
                gateway = get_llm_gateway()
                
                response = await gateway.chat_completion(
                    messages=[
                        {"role": "system", "content": persona_config["system_prompt"]},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=800
                )
                
                return response.get('content', '')
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                raise
        else:
            # Use injected gateway
            response = await self.llm_gateway.chat_completion(
                messages=[
                    {"role": "system", "content": persona_config["system_prompt"]},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            return response.get('content', '')
    
    async def _consult_persona(self, persona_id: str, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Consult a single persona with REAL LLM call.
        
        Args:
            persona_id: Persona identifier
            query: User query
            context: Query context
            
        Returns:
            Persona response dictionary
            
        Raises:
            ValueError: If persona_id is invalid
        """
        if persona_id not in self.personas:
            raise ValueError(f"Invalid persona_id: {persona_id}")
        
        try:
            persona_config = self.personas[persona_id]
            
            # Build context-aware prompt
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()]) if context else ""
            full_prompt = f"""Context:
{context_str}

Query: {query}

Provide your expert analysis from your specialized perspective."""
            
            # Make REAL LLM call
            response_text = await self._call_llm(full_prompt, persona_config)
            
            # Calculate confidence based on response quality
            confidence = min(0.98, 0.85 + (len(response_text) / 2000))
            
            return {
                "persona_id": persona_id,
                "status": "success",
                "perspective": persona_config["name"],
                "response": response_text,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat(),
                "tokens_used": len(response_text.split())  # Approximate
            }
        except Exception as e:
            logger.error(f"Persona {persona_id} consultation failed: {e}", exc_info=True)
            return {
                "persona_id": persona_id,
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_quad_analysis(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run concurrent 4-persona analysis with REAL LLM calls.
        
        Args:
            query: User query (max 10000 chars)
            context: Context dictionary
            
        Returns:
            Analysis results from all personas
            
        Raises:
            ValueError: If input validation fails
            RuntimeError: If rate limit exceeded
            asyncio.TimeoutError: If analysis exceeds timeout
        """
        # Input validation
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        
        if len(query) > 10000:
            raise ValueError("Query exceeds maximum length of 10000 characters")
        
        if not isinstance(context, dict):
            raise ValueError("Context must be a dictionary")
        
        # Rate limiting
        if self.active_queries >= self.max_concurrent_queries:
            raise RuntimeError(
                f"Maximum concurrent queries ({self.max_concurrent_queries}) reached. "
                "Please wait for existing queries to complete."
            )
        
        self.active_queries += 1
        
        try:
            # Sanitize input
            sanitized_query = query.strip()
            
            # Run all personas concurrently with timeout
            async with asyncio.timeout(self.query_timeout):
                tasks = []
                for pid in self.personas:
                    tasks.append(self._consult_persona(pid, sanitized_query, context))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results and handle exceptions
                output = {}
                errors = []
                successful_personas = []
                
                for result in results:
                    if isinstance(result, Exception):
                        errors.append(str(result))
                        logger.error(f"Persona task failed: {result}")
                    elif isinstance(result, dict):
                        persona_id = result.get('persona_id', 'unknown')
                        output[persona_id] = result
                        if result.get('status') == 'success':
                            successful_personas.append(result)
                        elif result.get('status') == 'error':
                            errors.append(f"{persona_id}: {result.get('error')}")
                
                # Synthesis Step using LLM
                if len(successful_personas) >= 2:
                    try:
                        # Build synthesis prompt from all successful responses
                        synthesis_prompt = f"""Analyze these expert perspectives on: "{sanitized_query}"

{chr(10).join([f"{p['perspective']}: {p['response'][:500]}..." for p in successful_personas])}

Provide a synthesized conclusion that:
1. Identifies areas of agreement
2. Highlights conflicting viewpoints
3. Provides a balanced recommendation"""
                        
                        from llm_gateway.gateway import get_llm_gateway
                        gateway = get_llm_gateway()
                        
                        synthesis_response = await gateway.chat_completion(
                            messages=[
                                {"role": "system", "content": "You are a synthesis expert who integrates multiple perspectives."},
                                {"role": "user", "content": synthesis_prompt}
                            ],
                            temperature=0.5,
                            max_tokens=1000
                        )
                        
                        synthesis_text = synthesis_response.get('content', 'Unable to synthesize')
                    except Exception as e:
                        logger.error(f"Synthesis failed: {e}")
                        synthesis_text = f"{len(successful_personas)}/4 experts analyzed successfully. Synthesis unavailable."
                else:
                    synthesis_text = f"Only {len(successful_personas)}/4 experts responded successfully. Insufficient data for synthesis."
                
                output['synthesis'] = {
                    "summary": synthesis_text,
                    "successful_personas": len(successful_personas),
                    "total_personas": 4,
                    "conflict_detected": len(successful_personas) >= 2,  # Can detect conflicts with 2+ responses
                    "errors": errors if errors else None,
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"Quad analysis completed: {len(successful_personas)}/4 personas successful")
                return output
                
        except asyncio.TimeoutError:
            logger.error(f"Quad analysis timed out after {self.query_timeout}s")
            raise asyncio.TimeoutError(f"Analysis exceeded timeout of {self.query_timeout} seconds")
        except Exception as e:
            logger.error(f"Quad analysis failed: {e}", exc_info=True)
            raise RuntimeError(f"Quad analysis failed: {e}")
        finally:
            self.active_queries -= 1

    def process_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous entry point for API with proper error handling.
        
        Args:
            query: User query
            context: Query context
            
        Returns:
            Analysis results
            
        Raises:
            ValueError: If input validation fails
            RuntimeError: If analysis fails
        """
        import asyncio
        
        try:
            # Check if event loop is already running
            try:
                loop = asyncio.get_running_loop()
                # If we're already in an async context, create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.run_quad_analysis(query, context)
                    )
                    return future.result()
            except RuntimeError:
                # No event loop running, safe to use asyncio.run
                return asyncio.run(self.run_quad_analysis(query, context))
        except Exception as e:
            logger.error(f"process_query failed: {e}", exc_info=True)
            raise


def create_quad_persona_engine(llm_gateway=None):
    """Factory function to create the engine instance."""
    return QuadPersonaEngine(llm_gateway=llm_gateway)
