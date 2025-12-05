"""
KA-49: Explainability Trace Constructor

This algorithm constructs detailed explanation traces for decisions,
creating transparent, human-readable pathways through complex reasoning processes.
"""

import logging
from typing import Dict, List, Any, Tuple
import time

logger = logging.getLogger(__name__)

class ExplainabilityTraceConstructor:
    """
    KA-49: Constructs transparent explanations for reasoning and decisions.
    
    This algorithm builds human-readable traces of decision processes,
    making complex reasoning patterns accessible and explainable.
    """
    
    def __init__(self):
        """Initialize the Explainability Trace Constructor."""
        self.explanation_formats = self._initialize_explanation_formats()
        self.trace_components = self._initialize_trace_components()
        logger.info("KA-49: Explainability Trace Constructor initialized")
    
    def _initialize_explanation_formats(self) -> Dict[str, Dict[str, Any]]:
        """Initialize formats for explanation traces."""
        return {
            "linear": {
                "description": "Step-by-step linear explanation",
                "structure": "sequential",
                "connector": " -> ",
                "audience_level": "general"
            },
            "tree": {
                "description": "Tree-structured explanation with branches",
                "structure": "hierarchical",
                "connector": " => ",
                "audience_level": "technical"
            },
            "narrative": {
                "description": "Story-like explanation with causal links",
                "structure": "causal",
                "connector": " therefore ",
                "audience_level": "general"
            },
            "contrastive": {
                "description": "Explanation contrasting alternatives",
                "structure": "comparative",
                "connector": " vs. ",
                "audience_level": "general"
            },
            "technical": {
                "description": "Detailed technical explanation",
                "structure": "detailed",
                "connector": "; ",
                "audience_level": "expert"
            }
        }
    
    def _initialize_trace_components(self) -> Dict[str, Dict[str, Any]]:
        """Initialize components for building traces."""
        return {
            "statement": {
                "description": "Factual statement or assertion",
                "template": "{content}",
                "examples": ["The user requested a time-series analysis", "The data shows seasonal patterns"]
            },
            "evidence": {
                "description": "Supporting evidence for a claim",
                "template": "Evidence: {content}",
                "examples": ["Evidence: 5 out of 7 data points exceed the threshold", "Evidence: The p-value is 0.03"]
            },
            "inference": {
                "description": "Logical inference or deduction",
                "template": "Therefore: {content}",
                "examples": ["Therefore: The model should include seasonality", "Therefore: The null hypothesis is rejected"]
            },
            "context": {
                "description": "Contextual information",
                "template": "Context: {content}",
                "examples": ["Context: This analysis is for financial forecasting", "Context: The user is a domain expert"]
            },
            "decision": {
                "description": "Decision made based on reasoning",
                "template": "Decision: {content}",
                "examples": ["Decision: Use ARIMA model", "Decision: Apply logarithmic transformation"]
            },
            "alternative": {
                "description": "Alternative option considered",
                "template": "Alternative: {content}",
                "examples": ["Alternative: Using neural networks", "Alternative: No data transformation"]
            },
            "uncertainty": {
                "description": "Expression of uncertainty",
                "template": "Uncertainty: {content}",
                "examples": ["Uncertainty: Confidence level 80%", "Uncertainty: Limited by sample size"]
            }
        }
    
    def construct_trace(self, decision_steps: List[str],
                      format_type: str = "linear",
                      audience: str = "general",
                      add_metadata: bool = True) -> Dict[str, Any]:
        """
        Construct explanation trace from decision steps.
        
        Args:
            decision_steps: List of decision step descriptions
            format_type: Format for the explanation trace
            audience: Intended audience for explanation
            add_metadata: Whether to add explanatory metadata
            
        Returns:
            Dictionary with explanation trace
        """
        # Validate inputs
        if not decision_steps:
            return {
                "error": "No decision steps provided",
                "success": False
            }
        
        # Get format information
        if format_type not in self.explanation_formats:
            format_type = "linear"  # Default to linear
        
        format_info = self.explanation_formats[format_type]
        
        # Process steps based on format
        if format_type == "linear":
            processed_steps, trace = self._process_linear_format(decision_steps, format_info["connector"])
        elif format_type == "tree":
            processed_steps, trace = self._process_tree_format(decision_steps, format_info["connector"])
        elif format_type == "narrative":
            processed_steps, trace = self._process_narrative_format(decision_steps, format_info["connector"])
        elif format_type == "contrastive":
            processed_steps, trace = self._process_contrastive_format(decision_steps, format_info["connector"])
        elif format_type == "technical":
            processed_steps, trace = self._process_technical_format(decision_steps, format_info["connector"])
        else:
            # Default to simple join
            processed_steps = decision_steps
            trace = format_info["connector"].join(decision_steps)
        
        # Prepare metadata
        metadata = None
        if add_metadata:
            metadata = self._generate_metadata(decision_steps, format_type, audience)
        
        # Create explanation result
        result = {
            "explanation_trace": trace,
            "format": format_type,
            "audience": audience,
            "steps_count": len(decision_steps),
            "processed_steps": processed_steps,
            "metadata": metadata
        }
        
        return result
    
    def _process_linear_format(self, steps: List[str], connector: str) -> Tuple[List[Dict[str, Any]], str]:
        """
        Process steps for linear format.
        
        Args:
            steps: List of decision steps
            connector: Connector string
            
        Returns:
            Tuple of (processed_steps, formatted_trace)
        """
        processed_steps = []
        
        for i, step in enumerate(steps):
            # Create step object
            step_obj = {
                "index": i + 1,
                "content": step,
                "type": self._infer_step_type(step)
            }
            
            processed_steps.append(step_obj)
        
        # Create trace
        trace = connector.join(step["content"] for step in processed_steps)
        
        return processed_steps, trace
    
    def _process_tree_format(self, steps: List[str], connector: str) -> Tuple[List[Dict[str, Any]], str]:
        """
        Process steps for tree format.
        
        Args:
            steps: List of decision steps
            connector: Connector string
            
        Returns:
            Tuple of (processed_steps, formatted_trace)
        """
        # For simplicity, we'll create a minimal tree structure
        # A real implementation would analyze dependencies between steps
        
        processed_steps = []
        
        # Create dummy tree structure
        tree_depth = min(2, len(steps) - 1) if len(steps) > 1 else 0
        
        for i, step in enumerate(steps):
            # Determine depth and parent
            if i == 0:
                depth = 0
                parent = None
            elif i <= tree_depth:
                depth = 1
                parent = 0
            else:
                depth = 2
                parent = 1 + ((i - tree_depth - 1) % tree_depth) if tree_depth > 0 else 0
            
            # Create step object
            step_obj = {
                "index": i + 1,
                "content": step,
                "type": self._infer_step_type(step),
                "depth": depth,
                "parent": parent
            }
            
            processed_steps.append(step_obj)
        
        # Create indented trace for tree visualization
        lines = []
        for step in processed_steps:
            indent = "  " * step["depth"]
            lines.append(f"{indent}{step['content']}")
        
        trace = "\n".join(lines)
        
        # Create alternate output with arrows
        if len(processed_steps) > 1:
            arrow_trace = processed_steps[0]["content"]
            for i in range(1, len(processed_steps)):
                arrow_trace += connector + processed_steps[i]["content"]
            
            # Use arrow trace if it's shorter
            if len(arrow_trace) < len(trace):
                trace = arrow_trace
        
        return processed_steps, trace
    
    def _process_narrative_format(self, steps: List[str], connector: str) -> Tuple[List[Dict[str, Any]], str]:
        """
        Process steps for narrative format.
        
        Args:
            steps: List of decision steps
            connector: Connector string
            
        Returns:
            Tuple of (processed_steps, formatted_trace)
        """
        processed_steps = []
        narrative_blocks = []
        
        for i, step in enumerate(steps):
            # Infer step type
            step_type = self._infer_step_type(step)
            
            # Create step object
            step_obj = {
                "index": i + 1,
                "content": step,
                "type": step_type
            }
            
            # Format step for narrative
            if step_type == "statement":
                narrative = f"First, {step.lower() if step[0].isupper() else step}"
            elif step_type == "evidence":
                narrative = f"We observed that {step.lower() if step[0].isupper() else step}"
            elif step_type == "inference":
                narrative = f"This led us to conclude that {step.lower() if step[0].isupper() else step}"
            elif step_type == "decision":
                narrative = f"Therefore, we decided to {step.lower() if step[0].isupper() else step}"
            else:
                narrative = step
            
            step_obj["narrative"] = narrative
            processed_steps.append(step_obj)
            narrative_blocks.append(narrative)
        
        # Create narrative trace
        trace = " ".join(narrative_blocks)
        
        return processed_steps, trace
    
    def _process_contrastive_format(self, steps: List[str], connector: str) -> Tuple[List[Dict[str, Any]], str]:
        """
        Process steps for contrastive format.
        
        Args:
            steps: List of decision steps
            connector: Connector string
            
        Returns:
            Tuple of (processed_steps, formatted_trace)
        """
        processed_steps = []
        
        # Group steps into main path and alternatives
        main_path = []
        alternatives = []
        
        for i, step in enumerate(steps):
            # Infer step type
            step_type = self._infer_step_type(step)
            
            # Create step object
            step_obj = {
                "index": i + 1,
                "content": step,
                "type": step_type
            }
            
            # Classify steps
            if step_type == "alternative":
                alternatives.append(step_obj)
            else:
                main_path.append(step_obj)
            
            processed_steps.append(step_obj)
        
        # Create contrastive trace
        if alternatives:
            # Format with explicit contrast
            main_content = " -> ".join(step["content"] for step in main_path)
            alt_content = ", ".join(step["content"] for step in alternatives)
            
            trace = f"Chosen path: {main_content}\nAlternatives considered: {alt_content}"
        else:
            # No alternatives, fall back to linear
            trace = " -> ".join(step["content"] for step in processed_steps)
        
        return processed_steps, trace
    
    def _process_technical_format(self, steps: List[str], connector: str) -> Tuple[List[Dict[str, Any]], str]:
        """
        Process steps for technical format.
        
        Args:
            steps: List of decision steps
            connector: Connector string
            
        Returns:
            Tuple of (processed_steps, formatted_trace)
        """
        processed_steps = []
        
        for i, step in enumerate(steps):
            # Infer step type
            step_type = self._infer_step_type(step)
            
            # Format step content for technical audience
            if step_type in self.trace_components:
                template = self.trace_components[step_type]["template"]
                tech_content = template.format(content=step)
            else:
                tech_content = step
            
            # Create step object
            step_obj = {
                "index": i + 1,
                "content": step,
                "technical_content": tech_content,
                "type": step_type
            }
            
            processed_steps.append(step_obj)
        
        # Create technical trace
        technical_steps = [step["technical_content"] for step in processed_steps]
        trace = connector.join(technical_steps)
        
        return processed_steps, trace
    
    def _infer_step_type(self, step: str) -> str:
        """
        Infer step type from content.
        
        Args:
            step: Step content
            
        Returns:
            Inferred step type
        """
        step_lower = step.lower()
        
        # Check for step type indicators
        if step_lower.startswith("therefore") or "conclude" in step_lower or "infer" in step_lower:
            return "inference"
        elif step_lower.startswith("evidence") or "observe" in step_lower or "data shows" in step_lower:
            return "evidence"
        elif step_lower.startswith("context") or "given that" in step_lower or "considering" in step_lower:
            return "context"
        elif step_lower.startswith("decision") or "choose" in step_lower or "select" in step_lower or "use" in step_lower:
            return "decision"
        elif step_lower.startswith("alternative") or "could have" in step_lower or "instead of" in step_lower:
            return "alternative"
        elif "uncertainty" in step_lower or "confidence" in step_lower or "probability" in step_lower:
            return "uncertainty"
        else:
            return "statement"
    
    def _generate_metadata(self, steps: List[str], format_type: str, audience: str) -> Dict[str, Any]:
        """
        Generate metadata for explanation trace.
        
        Args:
            steps: List of decision steps
            format_type: Format for the explanation trace
            audience: Intended audience for explanation
            
        Returns:
            Dictionary with metadata
        """
        # Count step types
        step_types = {}
        for step in steps:
            step_type = self._infer_step_type(step)
            step_types[step_type] = step_types.get(step_type, 0) + 1
        
        # Calculate explanation characteristics
        characteristics = {
            "complexity": min(1.0, len(steps) / 10),  # Scale complexity by step count
            "completeness": len(set(step_types)) / len(self.trace_components),
            "technical_depth": 0.8 if audience == "expert" else 0.5 if audience == "technical" else 0.3,
            "causal_strength": step_types.get("inference", 0) / len(steps) if steps else 0
        }
        
        # Generate interpretation guidance
        guidance = [
            f"This explanation is formatted as a {format_type} trace for {audience} audience.",
            f"It contains {len(steps)} steps across {len(set(step_types))} different reasoning types."
        ]
        
        # Add specific guidance based on format
        if format_type == "linear":
            guidance.append("Follow the steps in sequence to understand the reasoning path.")
        elif format_type == "tree":
            guidance.append("Each indentation level represents a branch in the reasoning tree.")
        elif format_type == "narrative":
            guidance.append("The explanation is presented as a narrative with causal connections.")
        elif format_type == "contrastive":
            guidance.append("The explanation contrasts the chosen path with alternatives that were considered.")
        elif format_type == "technical":
            guidance.append("This technical explanation includes specific category labels for each component.")
        
        # Prepare metadata
        metadata = {
            "step_types": step_types,
            "characteristics": characteristics,
            "interpretation_guidance": guidance,
            "audience_appropriateness": self._calculate_audience_appropriateness(steps, audience)
        }
        
        return metadata
    
    def _calculate_audience_appropriateness(self, steps: List[str], audience: str) -> float:
        """
        Calculate how appropriate the explanation is for the audience.
        
        Args:
            steps: List of decision steps
            audience: Intended audience for explanation
            
        Returns:
            Appropriateness score (0-1)
        """
        # Count technical terms
        technical_term_count = 0
        for step in steps:
            # This is a simplistic check, a real implementation would use NLP
            words = step.split()
            technical_term_count += sum(1 for word in words if len(word) > 8)  # Arbitrary heuristic
        
        # Calculate average step length
        avg_length = sum(len(step.split()) for step in steps) / len(steps) if steps else 0
        
        # Determine appropriateness
        if audience == "general":
            # Shorter steps, fewer technical terms better for general audience
            return max(0.0, min(1.0, 1.0 - (technical_term_count / (len(steps) * 2)) - (avg_length / 20)))
        elif audience == "technical":
            # Moderate technical content appropriate
            return max(0.0, min(1.0, (technical_term_count / (len(steps) * 2)) * 2 - 0.5))
        elif audience == "expert":
            # More technical terms, longer explanations better for experts
            return max(0.0, min(1.0, (technical_term_count / (len(steps) * 2)) + (avg_length / 15) - 0.3))
        else:
            return 0.5  # Default


def run(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the Explainability Trace Constructor (KA-49) on the provided data.
    
    Args:
        data: A dictionary containing decision steps to explain
        
    Returns:
        Dictionary with explanation trace
    """
    decision_steps = data.get("decision_steps", [])
    format_type = data.get("format", "linear")
    audience = data.get("audience", "general")
    add_metadata = data.get("add_metadata", True)
    
    # Simple case with just steps
    if isinstance(decision_steps, list) and all(isinstance(s, str) for s in decision_steps):
        if format_type == "linear" and audience == "general" and not add_metadata:
            trace = " -> ".join(decision_steps)
            return {
                "algorithm": "KA-49",
                "explanation_trace": trace,
                "timestamp": time.time(),
                "success": True
            }
    
    # Full trace construction
    constructor = ExplainabilityTraceConstructor()
    result = constructor.construct_trace(decision_steps, format_type, audience, add_metadata)
    
    if "error" in result:
        return {
            "algorithm": "KA-49",
            "error": result["error"],
            "success": False
        }
    
    return {
        "algorithm": "KA-49",
        "explanation_trace": result["explanation_trace"],
        "format": result["format"],
        "audience": result["audience"],
        "timestamp": time.time(),
        "success": True
    }