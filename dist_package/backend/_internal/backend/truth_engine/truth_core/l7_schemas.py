from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, UTC

class AGIBelief(BaseModel):
    """A unit of held knowledge or fact."""
    id: str
    content: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: str
    is_axiom: bool = False # If true, cannot be modified

class AGIGoal(BaseModel):
    """A recursive objective."""
    id: str
    content: str
    depth: int
    parent_id: Optional[str] = None
    sub_goals: List['AGIGoal'] = Field(default_factory=list)
    status: str = "pending" # pending, active, completed, failed
    probability_success: float = 0.5

class AGIConflict(BaseModel):
    """A detected contradiction between a Goal and a Belief."""
    id: str
    goal_id: str
    belief_id: str
    description: str
    severity: float = 0.5
    resolution: Optional[str] = None
    resolved: bool = False

class AGIPlan(BaseModel):
    """The output plan."""
    root_goal: AGIGoal
    conflicts: List[AGIConflict]
    convergence_score: float
    iterations: int
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

class AGIContext(BaseModel):
    """The full simulation state."""
    goals: List[AGIGoal]
    beliefs: List[AGIBelief]
    History: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
