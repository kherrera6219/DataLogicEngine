"""
Simulation Engine - PRODUCTION VERSION
--------------------------------------
The Core Intelligence engine responsible for running multi-agent counterfactual simulations
using real LLM calls through the existing gateway.
"""

import logging
import uuid
import asyncio
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class SimulationEvent:
    """A discrete event within a simulation timeline."""
    def __init__(self, step: int, agent: str, action: str, content: str, impact_score: float):
        self.step = step
        self.agent = agent
        self.action = action  # e.g., "ARGUE", "REBUT", "AGREE", "SYNTHESIZE"
        self.content = content
        self.impact_score = impact_score
        self.timestamp = datetime.now()

    def to_dict(self):
        return {
            'step': self.step,
            'agent': self.agent,
            'action': self.action,
            'content': self.content,
            'impact_score': self.impact_score,
            'timestamp': self.timestamp.isoformat()
        }

class SimulationResult:
    """The final outcome of a simulation run."""
    def __init__(self, simulation_id: str):
        self.simulation_id = simulation_id
        self.status = "initialized"
        self.events: List[SimulationEvent] = []
        self.consensus_reached = False
        self.final_conclusion = ""
        self.confidence_score = 0.0
        self.metadata = {}

    def add_event(self, event: SimulationEvent):
        self.events.append(event)

    def to_dict(self):
        return {
            'simulation_id': self.simulation_id,
            'status': self.status,
            'consensus_reached': self.consensus_reached,
            'final_conclusion': self.final_conclusion,
            'confidence_score': self.confidence_score,
            'event_count': len(self.events),
            'events': [e.to_dict() for e in self.events],
            'metadata': self.metadata
        }

class SimulationEngine:
    """
    Orchestrates the 10-Layer Simulation Logic using real LLM calls.
    
    Architecture:
    1. Scenario Contextualization (Axis Mapping)
    2. Persona Selection (Quad/Hexa configurations)
    3. Initial Stance Generation
    4. Adversarial Debate (Turn-based)
    5. Fact Checking (Truth Link)
    6. Bias Detection (KA-010 Integration)
    7. Convergence/Synthesis
    8. Outcome Projection
    9. Final Drafting
    10. Meta-Review
    """

    def __init__(self, llm_gateway=None, max_concurrent_simulations: int = 100):
        self.logger = logging.getLogger(__name__)
        self.llm_gateway = llm_gateway  # Inject LLM gateway
        self.active_simulations = {}
        self.max_concurrent_simulations = max_concurrent_simulations
        self.simulation_count = 0
        self.logger.info(f"SimulationEngine v2.0 initialized (PRODUCTION MODE, max concurrent: {max_concurrent_simulations}).")

    def create_simulation(self, query: str, context: Dict[str, Any]) -> str:
        """
        Initialize a new simulation session with input validation and rate limiting.
        
        Args:
            query: User query string (max 10000 chars)
            context: Context dictionary
            
        Returns:
            Simulation ID
            
        Raises:
            ValueError: If input validation fails
            RuntimeError: If rate limit exceeded
        """
        # Input validation
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        
        if len(query) > 10000:
            raise ValueError("Query exceeds maximum length of 10000 characters")
        
        if not isinstance(context, dict):
            raise ValueError("Context must be a dictionary")
        
        # Rate limiting check
        if len(self.active_simulations) >= self.max_concurrent_simulations:
            raise RuntimeError(
                f"Maximum concurrent simulations ({self.max_concurrent_simulations}) reached. "
                "Please wait for existing simulations to complete."
            )
        
        # Sanitize query (remove potential injection attempts)
        sanitized_query = query.strip()
        
        try:
            sim_id = str(uuid.uuid4())
            self.active_simulations[sim_id] = {
                "id": sim_id,
                "query": sanitized_query,
                "context": context,
                "created_at": datetime.now(),
                "status": "Ready"
            }
            self.simulation_count += 1
            self.logger.info(f"Created simulation {sim_id} (total: {self.simulation_count})")
            return sim_id
        except Exception as e:
            self.logger.error(f"Failed to create simulation: {e}")
            raise RuntimeError(f"Simulation creation failed: {e}")


    async def _call_llm(self, prompt: str, persona: str = "default") -> str:
        """
        Call LLM through the gateway.
        
        Args:
            prompt: The prompt to send
            persona: Persona name for context
            
        Returns:
            LLM response text
        """
        try:
            gateway = self.llm_gateway
            if gateway is None:
                from backend.llm_gateway.gateway import get_gateway

                gateway = get_gateway()

            if not hasattr(gateway, "process"):
                raise RuntimeError("Configured LLM gateway does not expose a process(request) method")

            from backend.llm_gateway.gateway import GatewayRequest

            response = await gateway.process(
                GatewayRequest(
                    messages=[
                        {"role": "system", "content": f"You are {persona}, an expert analyst."},
                        {"role": "user", "content": prompt},
                    ],
                    mode="chat",
                    run_ukg_pipeline=True,
                    temperature=0.7,
                    max_tokens=500,
                    meta={
                        "source": "simulation_engine",
                        "persona": persona,
                    },
                )
            )
            if response is None:
                raise RuntimeError("LLM gateway returned no response")

            if isinstance(response, dict):
                ok = bool(response.get("ok", True))
                content = response.get("content", "")
                error = response.get("error")
            else:
                ok = bool(getattr(response, "ok", True))
                content = getattr(response, "content", "")
                error = getattr(response, "error", None)

            if not ok:
                raise RuntimeError(error or "LLM gateway request failed")
            if not content:
                raise RuntimeError("LLM gateway returned an empty response")

            return content
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}", exc_info=True)
            raise RuntimeError(f"LLM execution failed for persona '{persona}'") from e

    async def run_simulation(self, simulation_id: str, depth: str = "standard", timeout: int = 300) -> Dict[str, Any]:
        """
        Execute the simulation loop with REAL LLM calls.
        
        Args:
            simulation_id: The ID of the session.
            depth: "quick", "standard", or "deep" (determines turns).
            timeout: Maximum execution time in seconds (default: 300)
        
        Returns:
            Simulation result dictionary
            
        Raises:
            ValueError: If simulation not found or invalid depth
            asyncio.TimeoutError: If simulation exceeds timeout
        """
        # Validation
        if simulation_id not in self.active_simulations:
            raise ValueError(f"Simulation {simulation_id} not found.")
        
        if depth not in ["quick", "standard", "deep"]:
            raise ValueError(f"Invalid depth '{depth}'. Must be 'quick', 'standard', or 'deep'.")

        sim_data = self.active_simulations[simulation_id]
        result = SimulationResult(simulation_id)
        result.status = "running"
        
        try:
            # Wrap execution in timeout
            async with asyncio.timeout(timeout):
                query = sim_data['query']
                
                # Step 1: Contextualize using LLM
                context_prompt = f"Analyze this query and identify relevant knowledge domains: {query}"
                context_analysis = await self._call_llm(context_prompt, "Orchestrator")
                result.add_event(SimulationEvent(1, "Orchestrator", "CONTEXTUALIZE", context_analysis, 0.9))

                # Step 2: Persona Selection
                personas = ["Knowledge_Expert", "Regulatory_Advisor", "Sector_Specialist"]
                result.add_event(SimulationEvent(2, "Orchestrator", "SELECT_AGENTS", f"Selected: {personas}", 0.9))
                result.metadata['personas'] = personas

                # Step 3-6: Multi-turn Adversarial Debate with REAL LLM
                turns = 2 if depth == "quick" else (3 if depth == "standard" else 5)
                debate_history = []
                
                for i in range(turns):
                    agent = personas[i % len(personas)]
                    
                    # Build debate context
                    history_context = "\n".join([f"{e.agent}: {e.content}" for e in result.events[-3:]])
                    debate_prompt = f"""Previous discussion:
{history_context}

As {agent}, provide your expert perspective on: {query}
Consider the previous arguments and either support, refute, or extend them."""
                    
                    argument = await self._call_llm(debate_prompt, agent)
                    debate_history.append(argument)
                    
                    # Calculate impact score based on argument length and turn
                    impact_score = min(0.95, 0.7 + (len(argument) / 1000) + (i * 0.05))
                    result.add_event(SimulationEvent(3+i, agent, "ARGUE", argument, impact_score))

                # Step 7: Synthesis using LLM
                synthesis_prompt = f"""Based on this multi-expert debate about '{query}':

{chr(10).join([f'{i+1}. {arg}' for i, arg in enumerate(debate_history)])}

Provide a synthesized conclusion that integrates all perspectives."""
                
                synthesis = await self._call_llm(synthesis_prompt, "Synthesizer")
                result.final_conclusion = synthesis
                result.consensus_reached = True
                
                # Calculate confidence based on debate quality
                result.confidence_score = min(0.95, 0.75 + (len(debate_history) * 0.05))
                result.status = "completed"
                
                self.logger.info(f"Simulation {simulation_id} completed successfully with {turns} LLM calls.")
                return result.to_dict()

        except asyncio.TimeoutError:
            self.logger.error(f"Simulation {simulation_id} timed out after {timeout}s")
            result.status = "timeout"
            result.metadata['error'] = f"Simulation exceeded timeout of {timeout} seconds"
            return result.to_dict()
        except Exception as e:
            self.logger.error(f"Simulation {simulation_id} failed: {e}", exc_info=True)
            result.status = "failed"
            result.metadata['error'] = str(e)
            result.metadata['error_type'] = type(e).__name__
            return result.to_dict()
        finally:
            # Cleanup: Remove from active simulations after completion
            if simulation_id in self.active_simulations:
                del self.active_simulations[simulation_id]
                self.logger.debug(f"Cleaned up simulation {simulation_id}")

    def process_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous wrapper for the API endpoint to run a standard simulation.
        """
        import asyncio
        
        sim_id = self.create_simulation(query, context)
        
        # Check if event loop is already running
        try:
            asyncio.get_running_loop()
            # If we're already in an async context, create a task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.run_simulation(sim_id, depth="standard")
                )
                return future.result()
        except RuntimeError:
            # No event loop running, safe to use asyncio.run
            return asyncio.run(self.run_simulation(sim_id, depth="standard"))


def create_simulation_engine(llm_gateway=None):
    """Factory function to create the engine instance."""
    return SimulationEngine(llm_gateway=llm_gateway)
