"""Integration layer for the Quad Persona mathematical framework."""

from datetime import UTC, datetime
from typing import Any, Dict, List, Tuple

import numpy as np

from core.persona.quad.mathematical_framework.memory_graph import StructuredMemoryGraph
from core.persona.quad.mathematical_framework.refinement import (
    DeepRecursiveLearning,
    RefinementWorkflow12Step,
)
from core.persona.quad.mathematical_framework.weights import (
    DynamicWeightFunctions,
    KnowledgeSpaceMapper,
)


class IntegrationFunction:
    """Integration Function Psi for synthesizing persona outputs."""

    def __init__(self, weight_functions: DynamicWeightFunctions = None):
        self.weight_functions = weight_functions or DynamicWeightFunctions()

    def integrate(
        self,
        persona_outputs: Dict[str, np.ndarray],
        context: Dict[str, Any],
        t: float = None,
    ) -> np.ndarray:
        """Apply integration function Psi."""
        weights = self.weight_functions.compute_all_weights(context, t)

        result = None
        for persona_type, output in persona_outputs.items():
            if persona_type in weights:
                weighted_output = weights[persona_type] * output
                if result is None:
                    result = weighted_output
                else:
                    result = result + weighted_output

        return result if result is not None else np.array([])

    def integrate_text(
        self,
        persona_outputs: Dict[str, str],
        context: Dict[str, Any],
        t: float = None,
    ) -> Tuple[str, Dict[str, float]]:
        """Integration for text outputs with weighted combination."""
        weights = self.weight_functions.compute_all_weights(context, t)

        sorted_personas = sorted(weights.items(), key=lambda x: x[1], reverse=True)

        combined_parts = []
        for persona_type, weight in sorted_personas:
            if persona_type in persona_outputs and weight > 0.1:
                output = persona_outputs[persona_type]
                if output:
                    combined_parts.append(f"[{persona_type.title()} Expert ({weight:.1%})]: {output}")

        return "\n\n".join(combined_parts), weights


class QuadPersonaMathematicalSystem:
    """Complete Quad Persona System with dynamic knowledge mapping."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        self.weight_functions = DynamicWeightFunctions(self.config.get("weights", {}))
        self.knowledge_mapper = KnowledgeSpaceMapper(
            relevance_threshold=self.config.get("relevance_threshold", 0.3)
        )
        self.memory_graph = StructuredMemoryGraph(
            memory_threshold=self.config.get("memory_threshold", 0.3)
        )
        self.recursive_learner = DeepRecursiveLearning(
            max_depth=self.config.get("max_depth", 12),
            epsilon=self.config.get("epsilon", 0.001),
        )
        self.integration = IntegrationFunction(self.weight_functions)
        self.refinement_workflow = RefinementWorkflow12Step()

        self.processing_history = []

    def process_full(
        self,
        query: str,
        context: Dict[str, Any] = None,
        t: float = None,
    ) -> Dict[str, Any]:
        """Complete system function QPS_full(q, c, t)."""
        context = context or {}

        query_embedding = self._embed_query(query)

        relevant_points = self.knowledge_mapper.map_query(query_embedding, context, t)

        persona_outputs = self._process_personas(query, context, t, relevant_points)

        initial_output = self.integration.integrate_text(persona_outputs, context, t)

        output_embedding = self._embed_query(initial_output[0])
        refined_output, iterations, drl_confidence = self.recursive_learner.deep_recursive_learning(
            output_embedding, context
        )

        workflow_input = {
            "query": query,
            "context": context,
            "persona_outputs": persona_outputs,
            "initial_output": initial_output[0],
            "weights": initial_output[1],
            "drl_iterations": iterations,
            "drl_confidence": drl_confidence,
        }

        final_output, final_confidence = self.refinement_workflow.apply_workflow(workflow_input)

        if not self.refinement_workflow.confidence_threshold_met(final_confidence):
            refined_output, iterations, drl_confidence = self.recursive_learner.deep_recursive_learning(
                refined_output, context
            )
            final_output["retry_drl"] = True
            final_output["final_drl_confidence"] = drl_confidence

        result = {
            "query": query,
            "final_output": final_output,
            "confidence": final_confidence,
            "threshold_met": self.refinement_workflow.confidence_threshold_met(final_confidence),
            "weights_used": initial_output[1],
            "relevant_points_count": len(relevant_points),
            "drl_iterations": iterations,
            "refinement_steps": self.refinement_workflow.step_results,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        self.processing_history.append(result)
        return result

    def _embed_query(self, text: str) -> np.ndarray:
        """Simple embedding for demonstration."""
        np.random.seed(hash(text) % (2**32))
        return np.random.randn(13)

    def _process_personas(
        self,
        query: str,
        context: Dict[str, Any],
        t: float,
        relevant_points: List,
    ) -> Dict[str, str]:
        """Process query through each persona function."""
        return {
            "knowledge": f"Knowledge analysis of: {query[:100]}...",
            "sector": f"Sector perspective on: {query[:100]}...",
            "regulatory": f"Regulatory considerations for: {query[:100]}...",
            "compliance": f"Compliance requirements for: {query[:100]}...",
        }

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system optimization metrics."""
        return {
            "total_queries": len(self.processing_history),
            "avg_confidence": np.mean([h["confidence"] for h in self.processing_history]) if self.processing_history else 0,
            "threshold_met_rate": sum(1 for h in self.processing_history if h["threshold_met"]) / len(self.processing_history) if self.processing_history else 0,
            "base_weights": self.weight_functions.base_weights,
            "knowledge_points_count": len(self.knowledge_mapper.knowledge_points),
            "memory_vertices_count": len(self.memory_graph.vertices),
        }
