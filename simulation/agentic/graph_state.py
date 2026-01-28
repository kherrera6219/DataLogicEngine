from typing import List, Dict, Any, TypedDict, Annotated
import operator

class UKGState(TypedDict):
    """
    State maintained across the agentic simulation graph.
    """
    # Inputs
    query: str
    context: Dict[str, Any]
    
    # Processing state (Annotated with operator.add to allow list accumulation)
    analysis_steps: Annotated[List[str], operator.add]
    confidence_history: Annotated[List[float], operator.add]
    layer_results: Dict[int, Any]
    
    # Meta
    current_layer: int
    max_layers: int
    simulation_id: str
    
    # Outputs
    final_output: str
    status: str
    confidence_overall: float
    next_node: str
