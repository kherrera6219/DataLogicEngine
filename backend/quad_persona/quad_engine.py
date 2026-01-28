"""
Quad Persona Engine
------------------
Runs concurrent analysis using 4 expert personas with comprehensive error handling and security.
"""

import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class QuadPersonaEngine:
    """
    Runs analyses concurrently using four distinct personas with security hardening.
    """
    
    def __init__(self, max_concurrent_queries: int = 50, query_timeout: int = 120):
        self.personas = {
            "knowledge": "Knowledge Expert (Axis 8)",
            "sector": "Sector Specialist (Axis 9)",
            "regulatory": "Regulatory Advisor (Axis 10)",
            "compliance": "Compliance Officer (Axis 11)"
        }
        self.max_concurrent_queries = max_concurrent_queries
        self.query_timeout = query_timeout
        self.active_queries = 0
        logger.info(f"QuadPersonaEngine initialized (max concurrent: {max_concurrent_queries}, timeout: {query_timeout}s).")
    
    async def _consult_persona(self, persona_id: str, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Consult a single persona with error handling.
        
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
            # Simulate persona consultation
            await asyncio.sleep(0.2)
            
            behavior = self.personas[persona_id]
            response_template = f"[{persona_id.upper()}] Analysis of '{query}' from {behavior} perspective."
            
            return {
                "persona_id": persona_id,
                "status": "success",
                "perspective": behavior,
                "response": response_template,
                "confidence": 0.95,
                "timestamp": datetime.now().isoformat()
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
        Run concurrent 4-persona analysis with comprehensive error handling.
        
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
                for result in results:
                    if isinstance(result, Exception):
                        errors.append(str(result))
                        logger.error(f"Persona task failed: {result}")
                    elif isinstance(result, dict):
                        persona_id = result.get('persona_id', 'unknown')
                        output[persona_id] = result
                        if result.get('status') == 'error':
                            errors.append(f"{persona_id}: {result.get('error')}")
                
                # Synthesis Step
                successful_personas = [p for p in output.values() if p.get('status') == 'success']
                output['synthesis'] = {
                    "summary": f"{len(successful_personas)}/4 experts analyzed the query successfully.",
                    "conflict_detected": False,
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


def create_quad_persona_engine():
    """Factory function to create the engine instance."""
    return QuadPersonaEngine()
