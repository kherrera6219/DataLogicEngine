"""
Multi-Agent Simulation Engine

Authoritative multi-agent counterfactual simulation using bounded provider calls.
This is the backend-layer engine for running adversarial multi-persona
debates and synthesizing conclusions through the LLM gateway.

The older engines under ``core/simulation`` are compatibility-only and are not
production entry points. This engine owns user-triggered simulation execution.
"""

import logging
import uuid
import asyncio
import inspect
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from backend.simulation.contracts import (
    SIMULATION_CONTRACT_VERSION,
    SIMULATION_ENGINE_ID,
    SIMULATION_ENGINE_VERSION,
    SimulationPlan,
)

logger = logging.getLogger(__name__)

class SimulationEvent:
    """A discrete event within a simulation timeline."""
    def __init__(self, step: int, agent: str, action: str, content: str, impact_score: Optional[float] = None):
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

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "SimulationEvent":
        return cls(
            int(payload.get("step") or 0),
            str(payload.get("agent") or "unknown"),
            str(payload.get("action") or "UNKNOWN"),
            str(payload.get("content") or ""),
            payload.get("impact_score"),
        )

class SimulationResult:
    """The final outcome of a simulation run."""
    def __init__(self, simulation_id: str):
        self.simulation_id = simulation_id
        self.status = "initialized"
        self.events: List[SimulationEvent] = []
        self.consensus_reached = False
        self.final_conclusion = ""
        self.confidence_score: Optional[float] = None
        self.validation = {"status": "not_measured", "validators": []}
        self.budget: Dict[str, Any] = {}
        self.metadata = {
            "contract_version": SIMULATION_CONTRACT_VERSION,
            "engine": SIMULATION_ENGINE_ID,
            "engine_version": SIMULATION_ENGINE_VERSION,
        }

    def add_event(self, event: SimulationEvent):
        self.events.append(event)

    def to_dict(self):
        return {
            'simulation_id': self.simulation_id,
            'status': self.status,
            'consensus_reached': self.consensus_reached,
            'final_conclusion': self.final_conclusion,
            'confidence_score': self.confidence_score,
            'validation': self.validation,
            'budget': self.budget,
            'event_count': len(self.events),
            'events': [e.to_dict() for e in self.events],
            'metadata': self.metadata
        }

class MultiAgentSimulationEngine:
    """
    Orchestrates multi-agent counterfactual simulations using bounded provider calls.

    Runs an adversarial multi-persona debate loop and synthesizes a conclusion.
    This is the sole production engine for user-triggered simulation routes.

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
        self.llm_gateway = llm_gateway
        self.active_simulations = {}
        self.max_concurrent_simulations = max_concurrent_simulations
        self.simulation_count = 0
        self.logger.info(
            "MultiAgentSimulationEngine v%s initialized (max concurrent: %s).",
            SIMULATION_ENGINE_VERSION,
            max_concurrent_simulations,
        )

    def create_simulation(
        self,
        query: str,
        context: Dict[str, Any],
        *,
        simulation_id: str | None = None,
    ) -> str:
        """
        Initialize a new simulation session with input validation and rate limiting.

        Returns:
            Simulation ID

        Raises:
            ValueError: If input validation fails
            RuntimeError: If rate limit exceeded
        """
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")

        if len(query) > 10000:
            raise ValueError("Query exceeds maximum length of 10000 characters")

        if not isinstance(context, dict):
            raise ValueError("Context must be a dictionary")

        if len(self.active_simulations) >= self.max_concurrent_simulations:
            raise RuntimeError(
                f"Maximum concurrent simulations ({self.max_concurrent_simulations}) reached. "
                "Please wait for existing simulations to complete."
            )

        sanitized_query = query.strip()

        try:
            sim_id = str(simulation_id or uuid.uuid4())
            if sim_id in self.active_simulations:
                raise ValueError("Simulation id is already active")
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
        """Use only the Phase 10 simulation-specific bounded provider adapter.

        Calling ``LLMGateway.process`` here would recursively start the complete
        governed workflow for every debate turn. Until Phase 10 selects and
        qualifies one simulation engine, no default provider adapter is wired.
        """

        adapter = self.llm_gateway
        if adapter is None or not hasattr(adapter, "generate_simulation_turn"):
            raise RuntimeError(
                "SIMULATION_PROVIDER_ADAPTER_UNAVAILABLE: bounded provider adapter is unavailable"
            )
        content = await adapter.generate_simulation_turn(
            prompt=prompt,
            persona=persona,
            max_tokens=500,
        )
        if not str(content or "").strip():
            raise RuntimeError("Simulation provider adapter returned an empty response")
        return str(content)

    async def run_simulation(
        self,
        simulation_id: str,
        depth: str = "standard",
        timeout: int = 300,
        *,
        resume_state: Dict[str, Any] | None = None,
        checkpoint_callback=None,
        plan: SimulationPlan | None = None,
    ) -> Dict[str, Any]:
        """
        Execute the simulation loop with real LLM calls.

        Raises:
            ValueError: If simulation not found or invalid depth
            asyncio.TimeoutError: If simulation exceeds timeout
        """
        if simulation_id not in self.active_simulations:
            raise ValueError(f"Simulation {simulation_id} not found.")

        plan = plan or SimulationPlan.for_depth(depth)

        sim_data = self.active_simulations[simulation_id]
        result = SimulationResult(simulation_id)
        result.status = "running"
        state = dict(resume_state or {})
        for event_payload in state.get("events") or []:
            if isinstance(event_payload, dict):
                result.add_event(SimulationEvent.from_dict(event_payload))

        async def checkpoint(step_key: str) -> None:
            if checkpoint_callback is None:
                return
            state["events"] = [event.to_dict() for event in result.events]
            payload = checkpoint_callback(step_key, dict(state))
            if inspect.isawaitable(payload):
                await payload

        try:
            async with asyncio.timeout(timeout):
                query = sim_data['query']
                supplied_evidence = list(
                    (sim_data.get("context") or {}).get("_simulation_evidence") or []
                )
                participant_specs = {
                    str(item.get("id")): item
                    for item in (
                        (sim_data.get("context") or {}).get("_simulation_participants") or []
                    )
                    if isinstance(item, dict) and item.get("id")
                }
                scenario_context = {
                    key: value
                    for key, value in (sim_data.get("context") or {}).items()
                    if not str(key).startswith("_simulation_")
                }
                scenario_context_block = json.dumps(
                    scenario_context,
                    sort_keys=True,
                    default=str,
                )
                evidence_block = "\n".join(
                    f"[{item.get('citation_label')}] {item.get('text')}"
                    for item in supplied_evidence
                    if isinstance(item, dict)
                )

                context_analysis = str(state.get("context_analysis") or "")
                if not context_analysis:
                    context_prompt = (
                        "Analyze this query and identify relevant knowledge domains. "
                        "Use only supplied evidence for factual claims and retain citation labels "
                        "in the form [S1]. State when evidence is insufficient.\n\n"
                        f"Query: {query}\n\nScenario context:\n"
                        f"{scenario_context_block or '{}'}\n\nSupplied evidence:\n"
                        f"{evidence_block or 'None'}"
                    )
                    context_analysis = await self._call_llm(context_prompt, "Orchestrator")
                    state["context_analysis"] = context_analysis
                    result.add_event(
                        SimulationEvent(1, "Orchestrator", "CONTEXTUALIZE", context_analysis)
                    )
                    await checkpoint("contextualize")

                personas = list(plan.participants)
                if not any(event.action == "SELECT_AGENTS" for event in result.events):
                    result.add_event(
                        SimulationEvent(2, "Orchestrator", "SELECT_AGENTS", f"Selected: {personas}")
                    )
                result.metadata['personas'] = personas

                turns = plan.debate_turns
                debate_history = [str(value) for value in state.get("debate_history") or []]

                for i in range(len(debate_history), turns):
                    agent = personas[i % len(personas)]
                    participant = participant_specs.get(agent) or {}
                    participant_context = "\n".join(
                        part
                        for part in (
                            (
                                f"Assigned role: {participant.get('role')}"
                                if participant.get("role")
                                else ""
                            ),
                            (
                                f"Perspective: {participant.get('perspective')}"
                                if participant.get("perspective")
                                else ""
                            ),
                        )
                        if part
                    )
                    history_context = "\n".join([f"{e.agent}: {e.content}" for e in result.events[-3:]])
                    debate_prompt = f"""Previous discussion:
{history_context}

As {agent}, provide your expert perspective on: {query}
{participant_context}
Consider the previous arguments and either support, refute, or extend them."""

                    argument = await self._call_llm(debate_prompt, agent)
                    debate_history.append(argument)

                    result.add_event(SimulationEvent(3+i, agent, "ARGUE", argument))
                    state["debate_history"] = list(debate_history)
                    await checkpoint(f"debate_{i + 1}")

                synthesis_prompt = f"""Based on this multi-expert debate about '{query}':

{chr(10).join([f'{i+1}. {arg}' for i, arg in enumerate(debate_history)])}

Provide a synthesized conclusion that integrates all perspectives. Preserve any
supplied evidence labels such as [S1] beside the claims they support. Do not add
labels or factual claims that were not present in the debate."""

                synthesis = str(state.get("final_conclusion") or "")
                if not synthesis:
                    synthesis = await self._call_llm(synthesis_prompt, "Synthesizer")
                    state["final_conclusion"] = synthesis
                    result.add_event(
                        SimulationEvent(3 + turns, "Synthesizer", "SYNTHESIZE", synthesis)
                    )
                    await checkpoint("synthesis")
                result.final_conclusion = synthesis
                result.consensus_reached = True

                usage_snapshot = getattr(self.llm_gateway, "usage_snapshot", None)
                result.budget = (
                    usage_snapshot()
                    if callable(usage_snapshot)
                    else {
                        "provider_calls_used": plan.max_provider_calls,
                        "max_provider_calls": plan.max_provider_calls,
                        "tokens_in": None,
                        "tokens_out": None,
                        "max_total_tokens": None,
                        "estimated_cost_usd": None,
                        "pricing_status": "not_measured",
                    }
                )
                result.metadata["plan"] = plan.to_dict()
                result.status = "completed"

                self.logger.info(
                    "Simulation %s completed successfully with %s provider calls.",
                    simulation_id,
                    plan.max_provider_calls,
                )
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
            if simulation_id in self.active_simulations:
                del self.active_simulations[simulation_id]
                self.logger.debug(f"Cleaned up simulation {simulation_id}")

    def process_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous wrapper for API endpoints."""
        import asyncio

        sim_id = self.create_simulation(query, context)

        try:
            asyncio.get_running_loop()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.run_simulation(sim_id, depth="standard")
                )
                return future.result()
        except RuntimeError:
            return asyncio.run(self.run_simulation(sim_id, depth="standard"))


def create_multi_agent_simulation_engine(llm_gateway=None) -> MultiAgentSimulationEngine:
    """Factory function to create a MultiAgentSimulationEngine instance."""
    return MultiAgentSimulationEngine(llm_gateway=llm_gateway)
